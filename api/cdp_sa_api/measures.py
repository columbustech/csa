class OverlapCoefficient():
    """Computes overlap coefficient measure.
    The overlap coefficient is a similarity measure related to the Jaccard
    measure  that measures the overlap between two sets, and is defined as the size of the intersection divided by
    the smaller of the size of the two sets. For two sets X and Y, the overlap coefficient is:
        :math:`overlap\\_coefficient(X, Y) = \\frac{|X \\cap Y|}{\\min(|X|, |Y|)}`
        
    Note:
        * In the case where one of X and Y is an empty set and the other is a non-empty set, we define their overlap coefficient to be 0.
        * In the case where both X and Y are empty sets, we define their overlap coefficient to be 1. 
    """

    def __init__(self):
        super(OverlapCoefficient, self).__init__()

    def get_raw_score(self, set1, set2):
        """Computes the raw overlap coefficient score between two sets.
        Args:
            set1,set2 (set or list): Input sets (or lists). Input lists are converted to sets.
        Returns:
            Overlap coefficient (float).
        Raises:
            TypeError : If the inputs are not sets (or lists) or if one of the inputs is None.
        Examples:
            >>> oc = OverlapCoefficient()
            >>> oc.get_raw_score(['data', 'science'], ['data'])
            1.0
            >>> oc.get_raw_score([], [])
            1.0
            >>> oc.get_raw_score([], ['data'])
            0
        References:
            * Wikipedia article : https://en.wikipedia.org/wiki/Overlap_coefficient
            * SimMetrics library
        """
        
        # input validations
        sim_check_for_none(set1, set2)
        sim_check_for_list_or_set_inputs(set1, set2)

        # if exact match return 1.0
        if sim_check_for_exact_match(set1, set2):
            return 1.0

        # if one of the strings is empty return 0
        if sim_check_for_empty(set1, set2):
            return 0

        if not isinstance(set1, set):
            set1 = set(set1)
        if not isinstance(set2, set):
            set2 = set(set2)

        return float(len(set1 & set2)) / min(len(set1), len(set2))

    def get_sim_score(self, set1, set2):
        """Computes the normalized overlap coefficient between two sets. Simply call get_raw_score. 
        Args:
            set1,set2 (set or list): Input sets (or lists). Input lists are converted to sets.
        Returns:
            Normalized overlap coefficient (float).
        Raises:
            TypeError : If the inputs are not sets (or lists) or if one of the inputs is None.
        Examples:
            >>> oc = OverlapCoefficient()
            >>> oc.get_sim_score(['data', 'science'], ['data'])
            1.0
            >>> oc.get_sim_score([], [])
            1.0
            >>> oc.get_sim_score([], ['data'])
            0
        """
        return self.get_raw_score(set1, set2)

class Jaccard():
    """Computes Jaccard measure.
     For two sets X and Y, the Jaccard similarity score is:
        :math:`jaccard(X, Y) = \\frac{|X \\cap Y|}{|X \\cup Y|}`
        
     Note:
         In the case where both X and Y are empty sets, we define their Jaccard score to be 1. 
    """

    def __init__(self):
        super(Jaccard, self).__init__()

    def get_raw_score(self, set1, set2):
        """Computes the raw Jaccard score between two sets.
        Args:
            set1,set2 (set or list): Input sets (or lists). Input lists are converted to sets.
        Returns:
            Jaccard similarity score (float).
        Raises:
            TypeError : If the inputs are not sets (or lists) or if one of the inputs is None.
        Examples:
            >>> jac = Jaccard()
            >>> jac.get_raw_score(['data', 'science'], ['data'])
            0.5
            >>> jac.get_raw_score({1, 1, 2, 3, 4}, {2, 3, 4, 5, 6, 7, 7, 8})
            0.375
            >>> jac.get_raw_score(['data', 'management'], ['data', 'data', 'science'])
            0.3333333333333333
        """
        
        # input validations
        sim_check_for_none(set1, set2)
        sim_check_for_list_or_set_inputs(set1, set2)

        # if exact match return 1.0
        if sim_check_for_exact_match(set1, set2):
            return 1.0

        # if one of the strings is empty return 0
        if sim_check_for_empty(set1, set2):
            return 0

        if not isinstance(set1, set):
            set1 = set(set1)
        if not isinstance(set2, set):
            set2 = set(set2)

        return float(len(set1 & set2)) / float(len(set1 | set2))

    def get_sim_score(self, set1, set2):
        """Computes the normalized Jaccard similarity between two sets. Simply call get_raw_score.
        Args:
            set1,set2 (set or list): Input sets (or lists). Input lists are converted to sets.
        Returns:
            Normalized Jaccard similarity (float).
        Raises:
            TypeError : If the inputs are not sets (or lists) or if one of the inputs is None.
        Examples:
            >>> jac = Jaccard()
            >>> jac.get_sim_score(['data', 'science'], ['data'])
            0.5
            >>> jac.get_sim_score({1, 1, 2, 3, 4}, {2, 3, 4, 5, 6, 7, 7, 8})
            0.375
            >>> jac.get_sim_score(['data', 'management'], ['data', 'data', 'science'])
            0.3333333333333333
        """
        return self.get_raw_score(set1, set2)
