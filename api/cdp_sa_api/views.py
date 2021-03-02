from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser

import os, requests, string, random, threading, logging, json
from .models import CSAJob
from .serializers import CSAJobSerializer
import copy
import py_cdrive_api
import nltk
from enum import Enum
from collections import Counter
import time

import sys
import re
from .tokenizers import QgramTokenizer, DelimiterTokenizer

from ast import literal_eval

import pandas as pd
from datasketch import MinHash, LeanMinHash

from .measures import Jaccard, OverlapCoefficient
import enum

overlap_coefficient = OverlapCoefficient()
jaccard = Jaccard()

class Type(enum.Flag):
    String = 1
    Numeric = 1 << 1
    Categorical = 1 << 2
    Textual = 1 << 3
    Datetime = 1 << 4

    @staticmethod
    def deserialize(string):
        s = string.replace('Type.', '')
        types = s.split('|')
        itype = Type.String
        for type in types:
            if type == 'Textual':
                itype = itype | Type.Textual
            elif type == 'Categorical':
                itype = itype | Type.Categorical
            elif type == 'Numeric':
                itype = itype | Type.Numeric
            elif type == 'Datetime':
                itype = itype | Type.Datetime
        return itype


def infer_type(series, sample=False, sample_size=1000, text_length=30, random_state=1):
    """
    Infers the type of the input series
    :param series: pandas series whose type needs to be inferred
    :param sample: boolean whether to sample the series or not
    :param sample_size: int specifying the sample size
    :param text_length: average length
    :param random_state: initial random state for
    :return: enum indicating the inferred type
    """
    series = series[series.notnull()]
    inferred_type = Type.String

    if sample and len(series) > sample_size:
        series = series.sample(series, n=sample_size, random_state=random_state)

    if series.dtype == 'int64' or series.dtype == 'float64':
        inferred_type = inferred_type | Type.Numeric

    # Need a good datetime re pattern instead of the following
    try:
        if series.dtype == 'object' and series.str.match(r'\d{4}-\d{2}-\d{2}').sum() == len(series):
            inferred_type = inferred_type | Type.Datetime
        elif series.dtype == 'object' and series.str.match(r'\d{1,2}/\d{1,2}/\d{4}').sum() == len(series):
            inferred_type = inferred_type | Type.Datetime
    except AttributeError:
        pass

    if series.astype(str).apply(lambda x: len(x)).mean() > text_length:
        inferred_type = inferred_type | Type.Textual

    if len(series.unique()) < 5:
        inferred_type = inferred_type | Type.Categorical

    return inferred_type

class ValueFrequency:
    def __init__(self, value_frequency_series):
        self.value_frequency_series = value_frequency_series

    def overlap(self, other, count=None):
        self_list = self.value_frequency_series.index.tolist()[0:count]
        other_list = other.value_frequency_series.index.tolist()[0:count]
        return overlap_coefficient.get_sim_score(self_list, other_list)

    def jaccard(self, other, count=None):
        self_list = self.value_frequency_series.index.tolist()[0:count]
        other_list = other.value_frequency_series.index.tolist()[0:count]
        return jaccard.get_sim_score(self_list, other_list)

    def __str__(self):
        return str(self.value_frequency_series.to_dict())

    @staticmethod
    def deserialize(string):
        if string == '' or string is None:
            vf = None
        else:
            vf = ValueFrequency(pd.Series(literal_eval(string)))
        return vf


class MinHashWrapper:
    def __init__(self):
        self.minhash = MinHash()

    def update(self, string):
        self.minhash.update(string)

    def make_lean(self):
        self.minhash = LeanMinHash(self.minhash)

    def jaccard(self, other):
        return self.minhash.jaccard(other.minhash)

    def __str__(self):
        buf = bytearray(self.minhash.bytesize())
        self.minhash.serialize(buf)
        return str(buf)

    @staticmethod
    def deserialize(string):
        if string is None or string == '':
            return None
        mh = MinHashWrapper()
        mh.minhash = LeanMinHash.deserialize(bytearray(literal_eval(string[10:-1])))
        return mh

class Profile(Enum):
    dataset = 0
    column = 1
    column_lower = 2
    word_tokens = 3
    three_gram_tokens = 4
    three_gram_nv_tokens = 5
    itype = 6
    common_words = 7
    mean_value = 8
    median_value = 9
    length = 10
    unique_count = 11
    name_three_grams_minhash = 12
    name_nv_three_grams_minhash = 13
    name_words_minhash = 14
    content_patterns_minhash = 15
    content_values_minhash = 16
    content_common_words_minhash = 17
    word_freq = 18
    sample = 19
    column_names_list = 20
    column_id = 21

    @staticmethod
    def names():
        return Profile.__dict__['_member_names_']

    @staticmethod
    def len():
        return len(Profile.names())

def get_common_words(series, stop_words, drop_symbol_translator):
    """
    Computes top 10 commonly used words of the given column of a series
    :param series: input series to find commonly used words
    :param drop_symbol_translator:
    :param stop_words:
    :return: top 10 commonly used words as a list
    """
    word_count = dict()

    for index, row in series.iteritems():
        if type(row) != str:
            continue

        words = row.split()

        for word in words:
            processed_word = word.translate(drop_symbol_translator)
            processed_word = processed_word.lower()
            if not processed_word or processed_word not in stop_words:
                if processed_word not in word_count:
                    word_count[processed_word] = 1
                else:
                    word_count[processed_word] += 1

    return [common_word for common_word, count in Counter(word_count).most_common(10)]

def get_pattern(value):
    """
    Extracts pattern out of the value specified
    :param value: Input value whose pattern is required
    :return: str pattern
    """
    # Need better regular expressions for doing this
    value = value if type(value) == str else str(value)
    value = re.sub(r'\d', '9', value)
    value = re.sub('[a-z]', 'x', value)
    value = re.sub(r'\(', '', value)
    value = re.sub(r'\)', ' ', value)
    value = re.sub(r'-', ' ', value)
    value = re.sub('[ ]{2,}', ' ', value)
    return value

def get_word_freq(series):
    ds = series.str.replace(r'[^a-zA-Z\s]', '')
    ds = ds[ds.notnull()]
    try:
        ds = pd.DataFrame(ds.str.split().tolist()).stack().reset_index(drop=True)
    except IndexError:
        return None
    return ValueFrequency(ds.str.lower().value_counts()[0:30])

def get_minhash(series):
    """
    Computes minhash signature of the given series
    :param series:
    :return:
    """
    mh = MinHashWrapper()
    for value in series:
        if type(value) == str:
            mh.update(value.lower().encode('utf8'))
        else:
            mh.update(str(value).lower().encode('utf8'))
    mh.make_lean()
    return mh

def map_column(df, column):
    from nltk.corpus import stopwords
    drop_symbol_translator = str.maketrans('', '', ',./\'\"\\:;[]{}-_?!~`@#$%^&*()')
    drop_vowel_translator = str.maketrans('', '', 'aeiou')
    stop_words = set(stopwords.words('english'))
    word_tokenizer = DelimiterTokenizer({'_'})
    three_gram_tokenizer = QgramTokenizer(qval=3)
    column_lower = column.lower()
    word_tokens = word_tokenizer.tokenize(column)
    three_gram_tokens = three_gram_tokenizer.tokenize(column_lower)
    three_gram_nv_tokens = three_gram_tokenizer.tokenize(column_lower.translate(drop_vowel_translator))
    itype = infer_type(df[column], random_state=10)
    common_words = get_common_words(df[column], stop_words, drop_symbol_translator) \
        if not (itype & Type.Numeric) and not (itype & Type.Datetime) else ['']
    if len(common_words) == 0:
        common_words = ['']
    series = df[column]
    values = list()
    for value in series:
        if type(value) == str:
            values.append(value.lower())
        else:
            values.append(str(value).lower())
    patterns = list(map(lambda x: get_pattern(x), values))
    ds = df[df[column].notnull()][column]
    ds = ds.sample(10) if len(ds) > 10 else ds
    sample = list()
    for value in ds:
        sample.append(str(value))
    trait = list()
    trait.append(df.index.name + '/' + column)
    trait.append(df.index.name)
    trait.append(column)
    trait.append(column_lower)
    trait.append(word_tokens)
    trait.append(three_gram_tokens)
    trait.append(three_gram_nv_tokens)
    trait.append(str(itype))
    trait.append(common_words)
    trait.append(str(df[column].mean()) if itype & Type.Numeric else '')
    trait.append(str(df[column].median()) if itype & Type.Numeric else '')
    trait.append(str(df[column].astype(str).str.len().mean()))
    trait.append(str(len(df[column].unique())))
    trait.append(str(get_minhash(three_gram_tokens)))
    trait.append(str(get_minhash(three_gram_nv_tokens)))
    trait.append(str(get_minhash(word_tokens)))
    trait.append(str(get_minhash(df[column].apply(lambda x: get_pattern(x)))))
    trait.append(str(get_minhash(df[column])))
    trait.append(str(get_minhash(common_words) if common_words else None))
    trait.append(str(get_word_freq(df[column])) if itype & Type.Textual else 'None')
    trait.append(sample)
    trait.append(list(df.columns))
    return trait

def map_table(df):
    nltk.download('stopwords')
    return [map_column(df, column) for column in df.columns]

def profile(df):
    columns = copy.deepcopy(Profile.names())
    columns.remove("column_id")
    columns.insert(0, "index")
    profile_df = pd.DataFrame(map_table(df), columns=columns)
    #profile_df["column_id"] = 0
    profile_df.set_index("index", drop=True, inplace=True)
    return profile_df

class CSAJobManager:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def split(self):
        csa_job = CSAJob.objects.filter(uid=self.uid)[0]
        csa_job.status = 'Running'
        csa_job.long_status = 'Executing'
        csa_job.stage = 'Split'
        csa_job.save()

        time.sleep(10)
        client = py_cdrive_api.Client(access_token=self.access_token)
        csa_apps_dir = 'users/{}/apps/csa'.format(os.environ['COLUMBUS_USERNAME'])
        job_dir = '{}/{}'.format(csa_apps_dir, self.uid)
        split_dir = '{}/{}'.format(job_dir, 'split')
        client.create_folder(csa_apps_dir, self.uid)
        client.create_folder(job_dir, 'split')
        relative_paths = client.list_files(self.input_path, recursive=True)
        json_list = json.dumps(list(map(lambda x: {'path': self.input_path + '/' + x} , relative_paths)))
        f = open('items.json', 'w')
        f.write(json_list)
        f.close()
        client.upload('items.json', split_dir)
        os.remove('items.json')

    def apply(self):
        csa_job = CSAJob.objects.filter(uid=self.uid)[0]
        csa_job.status = 'Running'
        csa_job.long_status = 'Executing'
        csa_job.stage = 'Apply'
        csa_job.save()
        time.sleep(10)

        client = py_cdrive_api.Client(access_token=self.access_token)
        csa_apps_dir = 'users/{}/apps/csa'.format(os.environ['COLUMBUS_USERNAME'])
        job_dir = '{}/{}'.format(csa_apps_dir, self.uid)
        apply_dir = '{}/{}'.format(job_dir, 'apply')
        parts_dir = '{}/{}'.format(apply_dir, 'parts')
        client.create_folder(job_dir,'apply')
        client.create_folder(apply_dir, 'parts')
        relative_paths = client.list_files(self.input_path, recursive=True)
        for i, relative_path in enumerate(relative_paths):
            file_url = client.file_url(self.input_path + '/' + relative_path)
            df = pd.read_csv(file_url, encoding='utf-8', header=0)
            df.index.name = relative_path
            of = profile(df)
            of.to_csv('part-' + str(i) + '.csv')
            client.upload('part-' + str(i) + '.csv', parts_dir)
            os.remove('part-' + str(i) + '.csv')

    def combine(self):
        csa_job = CSAJob.objects.filter(uid=self.uid)[0]
        csa_job.status = 'Running'
        csa_job.long_status = 'Executing'
        csa_job.stage = 'Combine'
        csa_job.save()
        
        client = py_cdrive_api.Client(access_token=self.access_token)
        job_dir = 'users/{}/apps/csa/{}'.format(os.environ['COLUMBUS_USERNAME'], self.uid)
        parts_dir = 'users/{}/apps/csa/{}/apply/parts'.format(os.environ['COLUMBUS_USERNAME'], self.uid)
        relative_paths = client.list_files(parts_dir, recursive=True)
        dfs = []
        for relative_path in relative_paths:
            file_url = client.file_url(parts_dir + '/' + relative_path)
            dfs.append(pd.read_csv(file_url))
        df = pd.concat(dfs, ignore_index=True)
        df.to_csv(os.path.basename(self.output_path))
        client.upload(os.path.basename(self.output_path), os.path.dirname(self.output_path))
        os.remove(os.path.basename(self.output_path))
        
        csa_job = CSAJob.objects.filter(uid=self.uid)[0]
        csa_job.status = 'Complete'
        csa_job.long_status = 'Job complete. Output saved to ' + self.output_path + ', intermediate output saved to ' + job_dir
        csa_job.stage = 'Combine'
        csa_job.save()

def execute_workflow(uid, token, data):
    os.mkdir(os.path.join(settings.DATA_PATH, uid))
    jm = CSAJobManager(
        uid = uid,
        access_token = token,
        input_path = data['inputPath'],
        output_path = data['outputPath']
    )
    jm.split()
    jm.apply()
    jm.combine()

class Specs(APIView):
    parser_class = (JSONParser,)

    def get(self, request):
        data = {
            'clientId': os.environ['COLUMBUS_CLIENT_ID'],
            'authUrl': os.environ['AUTHENTICATION_URL'],
            'cdriveUrl': os.environ['CDRIVE_URL'],
            'cdriveApiUrl': os.environ['CDRIVE_API_URL'],
            'username': os.environ['COLUMBUS_USERNAME'],
            'appName': os.environ['APP_NAME'],
            'appUrl': os.environ['APP_URL']
        }
        return Response(data, status=status.HTTP_200_OK)

class AuthenticationToken(APIView):
    parser_class = (JSONParser,)

    @csrf_exempt
    def post(self, request, format=None):
        code = request.data['code']
        redirect_uri = request.data['redirect_uri']
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': os.environ['COLUMBUS_CLIENT_ID'],
            'client_secret': os.environ['COLUMBUS_CLIENT_SECRET']
        }
        response = requests.post(url=os.environ['AUTHENTICATION_URL'] + 'o/token/', data=data)

        return Response(response.json(), status=response.status_code)

class ExecuteJob(APIView):
    parser_class = (JSONParser,)

    @csrf_exempt
    def post(self, request):
        auth_header = request.META['HTTP_AUTHORIZATION']
        token = auth_header.split()[1]

        uid = ''.join(random.choices(string.ascii_lowercase + string.digits,k=10))
        csa_job = CSAJob(uid=uid, status="Running", long_status="Running")
        csa_job.save()

        t = threading.Thread(target=execute_workflow, args=(uid, token, request.data))
        t.start()

        return Response({'uid':uid}, status=status.HTTP_200_OK)

class JobStatus(APIView):
    parser_class = (JSONParser,)

    def get(self, request):
        uid = request.query_params['uid']
        sm_job = CSAJob.objects.filter(uid=uid)[0]
        return Response(CSAJobSerializer(sm_job).data, status=status.HTTP_200_OK) 
