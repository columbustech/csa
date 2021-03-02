import re
import functools
import six
import sys
from six import string_types
from six.moves import xrange

class Tokenizer(object):
    """The root class for tokenizers.
    Args:
        return_set (boolean): A flag to indicate whether to return a set of
                              tokens instead of a bag of tokens (defaults to False). 
                              
    Attributes: 
        return_set (boolean): An attribute to store the flag return_set. 
    """
    
    def __init__(self, return_set=False):
        self.return_set = return_set

    def get_return_set(self):
        """Gets the value of the return_set flag.
        Returns:
            The boolean value of the return_set flag. 
        """
        return self.return_set

    def set_return_set(self, return_set):
        """Sets the value of the return_set flag.
        Args:
            return_set (boolean): a flag to indicate whether to return a set of tokens instead of a bag of tokens.
        """
        self.return_set = return_set
        return True

class DefinitionTokenizer(Tokenizer):
    """A class of tokenizers that uses a definition to find tokens, as opposed to using delimiters.
    
    Examples of definitions include alphabetical tokens, qgram tokens. Examples of delimiters include white space, punctuations.
    Args:
        return_set (boolean): A flag to indicate whether to return a set of
                              tokens instead of a bag of tokens (defaults to False).
                              
    Attributes: 
        return_set (boolean): An attribute to store the flag return_set. 
    """
    
    def __init__(self, return_set=False):
        super(DefinitionTokenizer, self).__init__(return_set)


def sim_check_for_none(*args):
    if len(args) > 0 and args[0] is None:
        raise TypeError("First argument cannot be None")
    if len(args) > 1 and args[1] is None:
        raise TypeError("Second argument cannot be None")

def sim_check_for_empty(*args):
    if len(args[0]) == 0 or len(args[1]) == 0:
        return True


def sim_check_for_same_len(*args):
    if len(args[0]) != len(args[1]):
        raise ValueError("Undefined for sequences of unequal length")


def sim_check_for_string_inputs(*args):
    if not isinstance(args[0], six.string_types):
        raise TypeError('First argument is expected to be a string')
    if not isinstance(args[1], six.string_types):
        raise TypeError('Second argument is expected to be a string')


def sim_check_for_list_or_set_inputs(*args):
    if not isinstance(args[0], list):
        if not isinstance(args[0], set):
            raise TypeError('First argument is expected to be a python list or set')
    if not isinstance(args[1], list):
        if not isinstance(args[1], set):
            raise TypeError('Second argument is expected to be a python list or set')


def sim_check_tversky_parameters(alpha, beta):
        if alpha < 0 or beta < 0:
            raise ValueError('Tversky parameters should be greater than or equal to zero')


def sim_check_for_exact_match(*args):
    if args[0] == args[1]:
        return True


def sim_check_for_zero_len(*args):
    if len(args[0].strip()) == 0 or len(args[1].strip()) == 0:
        raise ValueError("Undefined for string of zero length")


def tok_check_for_string_input(*args):
    for i in range(len(args)):
        if not isinstance(args[i], six.string_types):
            raise TypeError('Input is expected to be a string')


def tok_check_for_none(*args):
    if args[0] is None:
        raise TypeError("First argument cannot be None")


def convert_bag_to_set(input_list):
    seen_tokens = {}
    output_set =[]
    for token in input_list:
        if seen_tokens.get(token) == None:
            output_set.append(token)
            seen_tokens[token] = True
    return output_set


def convert_to_unicode(input_string):
    """Convert input string to unicode."""
    if isinstance(input_string, bytes):
        return input_string.decode('utf-8')
    return input_string 


def remove_non_ascii_chars(input_string):
    remove_chars = str("").join([chr(i) for i in range(128, 256)])
    translation_table = dict((ord(c), None) for c in remove_chars)
    return input_string.translate(translation_table)


def process_string(input_string, force_ascii=False):
    """Process string by
    -- removing all but letters and numbers
    -- trim whitespace
    -- converting string to lower case
    if force_ascii == True, force convert to ascii"""

    if force_ascii:
        input_string = remove_non_ascii_chars(input_string)

    regex = re.compile(r"(?ui)\W")

    # Keep only Letters and Numbers.
    out_string = regex.sub(" ", input_string)

    # Convert String to lowercase.
    out_string = out_string.lower()

    # Remove leading and trailing whitespaces.
    out_string = out_string.strip()
    return out_string

class DelimiterTokenizer(Tokenizer):
    """Uses delimiters to find tokens, as apposed to using definitions. 
    
    Examples of delimiters include white space and punctuations. Examples of definitions include alphabetical and qgram tokens. 
    Args:
        delim_set (set): A set of delimiter strings (defaults to space delimiter).
        return_set (boolean): A flag to indicate whether to return a set of
                              tokens instead of a bag of tokens (defaults to False).
                              
    Attributes: 
        return_set (boolean): An attribute to store the value of the flag return_set.
    """

    def __init__(self, 
                 delim_set=set([' ']), return_set=False):
        self.__delim_set = None
        self.__use_split = None
        self.__delim_str = None
        self.__delim_regex = None
        self._update_delim_set(delim_set)
        super(DelimiterTokenizer, self).__init__(return_set)

    def tokenize(self, input_string):
        """Tokenizes input string based on the set of delimiters.
        Args:
            input_string (str): The string to be tokenized. 
        Returns:
            A Python list which is a set or a bag of tokens, depending on whether return_set flag is set to True or False. 
        Raises:
            TypeError : If the input is not a string.
        Examples:
            >>> delim_tok = DelimiterTokenizer() 
            >>> delim_tok.tokenize('data science')
            ['data', 'science']
            >>> delim_tok = DelimiterTokenizer(['$#$']) 
            >>> delim_tok.tokenize('data$#$science')
            ['data', 'science']
            >>> delim_tok = DelimiterTokenizer([',', '.']) 
            >>> delim_tok.tokenize('data,science.data,integration.')
            ['data', 'science', 'data', 'integration']
            >>> delim_tok = DelimiterTokenizer([',', '.'], return_set=True) 
            >>> delim_tok.tokenize('data,science.data,integration.')
            ['data', 'science', 'integration']
        """
        tok_check_for_none(input_string)
        tok_check_for_string_input(input_string)
    
        if self.__use_split:
            token_list = list(filter(None,
                                     input_string.split(self.__delim_str)))
        else:
            token_list = list(filter(None,
                                     self.__delim_regex.split(input_string)))

        if self.return_set:
            return convert_bag_to_set(token_list)

        return token_list

    def get_delim_set(self):
        """Gets the current set of delimiters.
        
        Returns:
            A Python set which is the current set of delimiters. 
        """
        return self.__delim_set

    def set_delim_set(self, delim_set):
        """Sets the current set of delimiters.
        
        Args:
            delim_set (set): A set of delimiter strings.
        """
        return self._update_delim_set(delim_set)

    def _update_delim_set(self, delim_set):
        if not isinstance(delim_set, set):
            delim_set = set(delim_set)
        self.__delim_set = delim_set
        # if there is only one delimiter string, use split instead of regex
        self.__use_split = False
        if len(self.__delim_set) == 1:
            self.__delim_str = list(self.__delim_set)[0]
            self.__use_split = True
        else:
            self.__delim_regex = re.compile('|'.join(
                                     map(re.escape, self.__delim_set)))
        return True

class QgramTokenizer(DefinitionTokenizer):
    """Returns tokens that are sequences of q consecutive characters.
    
    A qgram of an input string s is a substring t (of s) which is a sequence of q consecutive characters. Qgrams are also known as
    ngrams or kgrams. 
    Args:
        qval (int): A value for q, that is, the qgram's length (defaults to 2).
        return_set (boolean): A flag to indicate whether to return a set of
                              tokens or a bag of tokens (defaults to False).
        padding (boolean): A flag to indicate whether a prefix and a suffix should be added
                           to the input string (defaults to True).
        prefix_pad (str): A character (that is, a string of length 1 in Python) that should be replicated 
                          (qval-1) times and prepended to the input string, if padding was 
                          set to True (defaults to '#').
        suffix_pad (str): A character (that is, a string of length 1 in Python) that should be replicated 
                          (qval-1) times and appended to the input string, if padding was 
                          set to True (defaults to '$').
    Attributes:
        qval (int): An attribute to store the q value.
        return_set (boolean): An attribute to store the flag return_set.
        padding (boolean): An attribute to store the padding flag.
        prefix_pad (str): An attribute to store the prefix string that should be used for padding.
        suffix_pad (str): An attribute to store the suffix string that should
                          be used for padding.
    """

    def __init__(self, qval=2,
                 padding=True, prefix_pad='#', suffix_pad='$',
                 return_set=False):
        if qval < 1:
            raise AssertionError("qval cannot be less than 1")
        self.qval = qval

        if not type(padding) == type(True):
            raise AssertionError('padding is expected to be boolean type')
        self.padding = padding

        if not isinstance(prefix_pad, string_types):
            raise AssertionError('prefix_pad is expected to be of type string')
        if not isinstance(suffix_pad, string_types):
            raise AssertionError('suffix_pad is expected to be of type string')
        if not len(prefix_pad) == 1:
            raise AssertionError("prefix_pad should have length equal to 1")
        if not len(suffix_pad) == 1:
            raise AssertionError("suffix_pad should have length equal to 1")

        self.prefix_pad = prefix_pad
        self.suffix_pad = suffix_pad

        super(QgramTokenizer, self).__init__(return_set)

    def tokenize(self, input_string):
        """Tokenizes input string into qgrams.
        Args:
            input_string (str): The string to be tokenized. 
        Returns:
            A Python list, which is a set or a bag of qgrams, depending on whether return_set flag is True or False. 
        Raises:
            TypeError : If the input is not a string
        Examples:
            >>> qg2_tok = QgramTokenizer()
            >>> qg2_tok.tokenize('database')
            ['#d', 'da', 'at', 'ta', 'ab', 'ba', 'as', 'se', 'e$']
            >>> qg2_tok.tokenize('a')
            ['#a', 'a$']
            >>> qg3_tok = QgramTokenizer(qval=3)
            >>> qg3_tok.tokenize('database')
            ['##d', '#da', 'dat', 'ata', 'tab', 'aba', 'bas', 'ase', 'se$', 'e$$']
            >>> qg3_nopad = QgramTokenizer(padding=False)
            >>> qg3_nopad.tokenize('database')
            ['da', 'at', 'ta', 'ab', 'ba', 'as', 'se']
            >>> qg3_diffpads = QgramTokenizer(prefix_pad='^', suffix_pad='!')
            >>> qg3_diffpads.tokenize('database')
            ['^d', 'da', 'at', 'ta', 'ab', 'ba', 'as', 'se', 'e!']
                      
        """
        tok_check_for_none(input_string)
        tok_check_for_string_input(input_string)

        qgram_list = []

        # If the padding flag is set to true, add q-1 "prefix_pad" characters
        # in front of the input string and  add q-1 "suffix_pad" characters at
        # the end of the input string.
        if self.padding:
            input_string = (self.prefix_pad * (self.qval - 1)) + input_string \
                           + (self.suffix_pad * (self.qval - 1))

        if len(input_string) < self.qval:
            return qgram_list

        qgram_list = [input_string[i:i + self.qval] for i in
                      xrange(len(input_string) - (self.qval - 1))]
        qgram_list = list(filter(None, qgram_list))

        if self.return_set:
            return convert_bag_to_set(qgram_list)

        return qgram_list

    def get_qval(self):
        """Gets the value of the qval attribute, which is the length of qgrams. 
        Returns:
            The value of the qval attribute. 
        """
        return self.qval

    def set_qval(self, qval):
        """Sets the value of the qval attribute. 
        Args:
            qval (int): A value for q (the length of qgrams). 
        Raises:
            AssertionError : If qval is less than 1.
        """
        if qval < 1:
            raise AssertionError("qval cannot be less than 1")
        self.qval = qval
        return True

    def get_padding(self):
        """
        Gets the value of the padding flag. This flag determines whether the
        padding should be done for the input strings or not.
        Returns:
            The Boolean value of the padding flag.
        """
        return self.padding

    def set_padding(self, padding):
        """
        Sets the value of the padding flag.
        Args:
            padding (boolean): Flag to indicate whether padding should be
                done or not.
        Returns:
            The Boolean value of True is returned if the update was
            successful.
        Raises:
            AssertionError: If the padding is not of type boolean
        """
        if not type(padding) == type(True):
            raise AssertionError('padding is expected to be boolean type')
        self.padding = padding
        return True

    def get_prefix_pad(self):
        """
        Gets the value of the prefix pad.
        Returns:
            The prefix pad string.
        """
        return self.prefix_pad

    def set_prefix_pad(self, prefix_pad):
        """
        Sets the value of the prefix pad string.
        Args:
            prefix_pad (str): String that should be prepended to the
                input string before tokenization.
        Returns:
            The Boolean value of True is returned if the update was
            successful.
        Raises:
            AssertionError: If the prefix_pad is not of type string.
            AssertionError: If the length of prefix_pad is not one.
        """
        if not isinstance(prefix_pad, string_types):
            raise AssertionError('prefix_pad is expected to be of type string')
        if not len(prefix_pad) == 1:
            raise AssertionError("prefix_pad should have length equal to 1")
        self.prefix_pad = prefix_pad
        return True

    def get_suffix_pad(self):
        """
        Gets the value of the suffix pad.
        Returns:
            The suffix pad string.
        """
        return self.suffix_pad

    def set_suffix_pad(self, suffix_pad):
        """
        Sets the value of the suffix pad string.
        Args:
            suffix_pad (str): String that should be appended to the
                input string before tokenization.
        Returns:
            The boolean value of True is returned if the update was
            successful.
        Raises:
            AssertionError: If the suffix_pad is not of type string.
            AssertionError: If the length of suffix_pad is not one.
        """
        if not isinstance(suffix_pad, string_types):
            raise AssertionError('suffix_pad is expected to be of type string')
        if not len(suffix_pad) == 1:
            raise AssertionError("suffix_pad should have length equal to 1")
        self.suffix_pad = suffix_pad
        return True
