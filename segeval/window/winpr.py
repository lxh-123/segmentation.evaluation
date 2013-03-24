'''
Implementation of the WinPR segmentation evaluation metric described in Scaiano
and Inkpen (2012).

.. moduleauthor:: Chris Fournier <chris.m.fournier@gmail.com>
'''
from .windowdiff import compute_window_size
from ..ml import fmeasure, precision, recall, cf_to_vars, vars_to_cf
from ..ml.fbmeasure import parser_beta_support, DEFAULT_BETA
from .. import SegmentationMetricError, compute_pairwise, \
    convert_masses_to_positions, compute_pairwise_values, create_tsv_rows
from ..data import load_file
from ..data.tsv import write_tsv
from ..data.display import render_mean_values, render_mean_micro_values, \
     render_permuted


DEFAULT_PERMUTED = False


def create_paired_window(hypothesis_positions, reference_positions, window_size,
                  lamprier_et_al_2007_fix):
    '''
    Create a set of pairs of units from each segmentation to go over using a
    window.
    '''
    phantom_size = 0
    if lamprier_et_al_2007_fix is False:
        units_ref_hyp = zip(reference_positions, hypothesis_positions)
    else:
        phantom_size = window_size
        phantom_size = 1 if phantom_size <= 0 else phantom_size
        phantom_hyp_start = [int(hypothesis_positions[0])]  * phantom_size
        phantom_hyp_end   = [int(hypothesis_positions[-1])] * phantom_size
        phantom_ref_start = [int(reference_positions[0])]   * phantom_size
        phantom_ref_end   = [int(reference_positions[-1])]  * phantom_size
        units_ref_hyp = \
            zip(phantom_ref_start + reference_positions  + phantom_ref_end,
                phantom_hyp_start + hypothesis_positions + phantom_hyp_end)
    return units_ref_hyp, phantom_size


def win_pr(hypothesis_positions, reference_positions, window_size=None,
           convert_from_masses=True):
    '''
    Calculates the WinPR segmentation evaluation metric confusion matrix for a
    hypothetical segmentation against a reference segmentation for a given
    window size.  The standard WindowDiff method of calculating the window size
    is performed when a window size is not specified.
    
    :param hypothesis_positions:     Hypothesis segmentation section labels
                                        sequence.
    :param reference_positions:      Reference segmentation section labels
                                        sequence.
    :param window_size:              The size of the window that is slid over \
                                        the two segmentations used to count \
                                        mismatches (default is None and will \
                                        use the average window size)
    :param return_fscore:            If True, specifies that an F-score is to \
                                        be returned.
    :param convert_from_masses:      Convert the segmentations provided from \
                                        masses into positions.
    :type hypothesis_positions: list
    :type reference_positions: list
    :type window_size: int
    :type convert_from_masses: bool
    
    :returns: TP, FP, FN, TN
    :rtype: :func:`int`, :func:`int`, :func:`int`, :func:`int`
    '''
    # pylint: disable=C0103, R0914
    # Convert from masses into positions 
    if convert_from_masses:
        reference_positions  = convert_masses_to_positions(reference_positions)
        hypothesis_positions = convert_masses_to_positions(hypothesis_positions)
    # Check for input errors
    if len(reference_positions) is not len(hypothesis_positions):
        raise SegmentationMetricError(
                    'Reference and hypothesis segmentations differ in position \
length (%(ref)i is not %(hyp)i).' % {'ref' : len(reference_positions),
                                 'hyp' : len(hypothesis_positions)})
    # Compute window size to use if unspecified
    if window_size is None:
        window_size = compute_window_size(reference_positions)
    # Create a set of pairs of units from each segmentation to go over using a
    # window
    tp, fp, fn = [0] * 3
    tn = (-1 * window_size) * (window_size * 2 + 1)
    # Create and append phantom boundaries at the beginning and end of the
    # segmentation to properly count boundaries at the beginning and end
    units_ref_hyp = create_paired_window(hypothesis_positions,
                                         reference_positions, window_size,
                                         lamprier_et_al_2007_fix = True)[0]
    # Slide window over and calculate TP, TN, FP, FN
    measurements = len(units_ref_hyp) - (window_size + 1)
    for i in xrange(0, measurements):
        window = units_ref_hyp[i:i + window_size + 1]
        ref_boundaries = 0
        hyp_boundaries = 0
        # Check that the number of loops is correct
        if len(window) is not window_size + 1:
            raise SegmentationMetricError('Incorrect actual window size')
        # For pair in window
        for j in xrange(0, len(window) - 1):
            ref_part, hyp_part = zip(*window[j:j + 2])
            # Boundary exists in the reference segmentation
            if ref_part[0] is not ref_part[1]:
                ref_boundaries += 1
            # Boundary exists in the hypothesis segmentation
            if hyp_part[0] is not hyp_part[1]:
                hyp_boundaries += 1
        # If the number of boundaries per segmentation in the window differs
        tp += min(ref_boundaries, hyp_boundaries)
        fp += max(0, hyp_boundaries - ref_boundaries)
        fn += max(0, ref_boundaries - hyp_boundaries)
        tn += (window_size - max(ref_boundaries, hyp_boundaries))
    # Return the constituent statistics
    return vars_to_cf(tp, fp, fn, tn)


def win_pr_f(hypothesis_positions, reference_positions, window_size=None,
             convert_from_masses=False, beta=DEFAULT_BETA):
    '''
    Compute F_beta Measure from WinPR.
    
    .. seealso:: :func:`win_pr`
    .. seealso:: :func:`segeval.ml.fmeasure`
    '''
    # pylint: disable=C0103
    cf = win_pr(hypothesis_positions, reference_positions,
                            window_size, convert_from_masses)
    return fmeasure(cf, beta)


def wrap_win_p_f(beta=DEFAULT_BETA):
    '''
    Create a wrapper for win_pr_f
    '''
    def wrapper(hypothesis_masses, reference_masses, window_size,
                convert_from_masses):
        '''
        Wrapper to provide the beta parameter.
        '''
        return win_pr_f(hypothesis_masses, reference_masses, window_size,
                        convert_from_masses, beta=beta)
    return wrapper


def win_pr_p(hypothesis_positions, reference_positions, window_size=None,
             convert_from_masses=False):
    '''
    Compute Precision from WinPR.
    
    .. seealso:: :func:`win_pr`
    .. seealso:: :func:`segeval.ml.precision`
    '''
    # pylint: disable=C0103
    cf = win_pr(hypothesis_positions, reference_positions, window_size,
                convert_from_masses)
    return precision(cf)


def win_pr_r(hypothesis_positions, reference_positions, window_size=None,
             convert_from_masses=False):
    '''
    Compute Recall from WinPR.
    
    .. seealso:: :func:`win_pr`
    .. seealso:: :func:`segeval.ml.recall`
    '''
    # pylint: disable=C0103
    cf = win_pr(hypothesis_positions, reference_positions, window_size,
                convert_from_masses)
    return recall(cf)


def pairwise_win_pr(dataset_masses,
                    fnc_winpr=win_pr_f,
                    window_size=None,
                    convert_from_masses=True):
    '''
    Calculate mean pairwise WinPR-F_beta, WinPR-P, or WinPR-R.
    
    .. seealso:: :func:`win_pr`
    .. seealso:: :func:`segeval.compute_pairwise`
    
    :param dataset_masses: Segmentation mass dataset (including multiple \
                           codings).
    :type dataset_masses: dict
        
    :returns: Mean, standard deviation, variance, and standard error of a \
        segmentation metric.
    :rtype: :class:`decimal.Decimal`, :class:`decimal.Decimal`, \
        :class:`decimal.Decimal`, :class:`decimal.Decimal`
    '''
    def wrapper(hypothesis_masses, reference_masses):
        '''
        Wrapper to provide parameters.
        '''
        return fnc_winpr(hypothesis_masses, reference_masses, window_size,
                         convert_from_masses)
    
    return compute_pairwise(dataset_masses, wrapper, permuted=DEFAULT_PERMUTED)


def pairwise_win_pr_micro(dataset_masses, ml_fnc=fmeasure):
    '''
    Computes the mean (micro) of a particular ml metric.
    
    .. seealso:: :func:`f_b_measure`
    
    :param dataset_masses: Segmentation mass dataset (including multiple \
                           codings).
    :type dataset_masses: dict
        
    :returns: Mean (micro)
    :rtype: :class:`decimal.Decimal`
    '''
    # pylint: disable=C0103
    
    pairs = compute_pairwise_values(dataset_masses, win_pr)
    
    tp, fp, fn, tn = 0, 0, 0, 0
    for values in pairs.values():
        cur_tp, cur_fp, cur_fn, cur_tn = cf_to_vars(values)
        tp += cur_tp
        fp += cur_fp
        fn += cur_fn
        tn += cur_tn
    
    return ml_fnc(vars_to_cf(tp, fp, fn, tn))


OUTPUT_NAME = render_permuted('Mean WinPR value', DEFAULT_PERMUTED)
SHORT_NAME  = 'WinPR-%s'
SHORT_NAME_F  = 'F_%s'
SHORT_NAME_P  = 'P'
SHORT_NAME_R  = 'R'
SUBSUBPARSER_NAME_F = 'f'
SUBSUBPARSER_NAME_P = 'p'
SUBSUBPARSER_NAME_R = 'r'


def values_win_pr(dataset_masses, beta=DEFAULT_BETA):
    '''
    Produces a TSV for this metric
    '''
    # pylint: disable=C0103
    # Define a fnc to retrieve F_Beta-Measure values
    def wrapper_winpr(hypothesis_masses, reference_masses):
        '''
        Wrapper to provide parameters.
        '''
        # pylint: disable=W0613
        return win_pr(hypothesis_masses, reference_masses,
                      convert_from_masses=True)
    # Create header
    header = list(['coder1', 'coder2',
                   SHORT_NAME % SHORT_NAME_F + '_' + str(beta),
                   SHORT_NAME_P, SHORT_NAME_R, 'TP', 'FP', 'FN', 'TN'])
    # Calculate values
    values_cf = compute_pairwise_values(dataset_masses, wrapper_winpr,
                                        permuted=DEFAULT_PERMUTED)
    # Combine into one table
    combined_values = dict()
    for label, cf in values_cf.items():
        row = list()
        row.append(fmeasure(cf, beta))
        row.append(precision(cf))
        row.append(recall(cf))
        row.extend(cf_to_vars(cf))
        
        combined_values[label] = row
    # Return
    return create_tsv_rows(header, combined_values)


def parse(args):
    '''
    Parse this module's metric arguments and perform requested actions.
    '''
    # pylint: disable=C0103,R0914
    output = None
    values = load_file(args)
    subsubparser_name = args['subsubparser_name']
    name = SHORT_NAME % subsubparser_name
    beta = 1
    mean = None
    micro = args['micro']
    if 'beta' in args and args['beta'] is not 1:
        beta = args['beta']
    # Is a TSV requested?
    if args['output'] is not None:
        # Create a TSV
        output_file = args['output'][0]
        header, rows = values_win_pr(values, beta)
        write_tsv(output_file, header, rows)
    elif micro:
        # Create a string to output
        if subsubparser_name is SUBSUBPARSER_NAME_F:
            def wrapper(cf):
                '''
                Wrap ``ml_fmeasure`` so that it uses beta.
                '''
                return fmeasure(cf, beta)
            mean = pairwise_win_pr_micro(values, ml_fnc=wrapper)
            name = SHORT_NAME_F % str(beta)
        elif subsubparser_name is SUBSUBPARSER_NAME_P:
            mean = pairwise_win_pr_micro(values, ml_fnc=precision)
            name = SHORT_NAME_P
        elif subsubparser_name is SUBSUBPARSER_NAME_R:
            mean = pairwise_win_pr_micro(values, ml_fnc=recall)
            name = SHORT_NAME_R
        output = render_mean_micro_values(name, mean)
    else:
        # Create a string to output
        if subsubparser_name is SUBSUBPARSER_NAME_F:
            name += '_%s' % str(beta)
            mean, std, var, stderr, n = pairwise_win_pr(values,
                                                        wrap_win_p_f(beta))
        elif subsubparser_name is SUBSUBPARSER_NAME_P:
            mean, std, var, stderr, n = pairwise_win_pr(values, win_pr_p)
        elif subsubparser_name is SUBSUBPARSER_NAME_R:
            mean, std, var, stderr, n = pairwise_win_pr(values, win_pr_r)
        output = render_mean_values(name, mean, std, var, stderr, n)
    # Return
    return output

    
def create_submetric_parser(subparsers):
    '''
    Setup a command line parser for this module's sub metrics.
    '''
    from ..data import parser_add_file_support
    from .. import parser_micro_support
    
    parser_f = subparsers.add_parser(SUBSUBPARSER_NAME_F, help='F_beta Measure')
    parser_beta_support(parser_f)
    parser_add_file_support(parser_f)
    parser_micro_support(parser_f)
    parser_f.set_defaults(func=parse)
    
    parser_r = subparsers.add_parser(SUBSUBPARSER_NAME_R, help='Recall')
    parser_add_file_support(parser_r)
    parser_micro_support(parser_r)
    parser_r.set_defaults(func=parse)
    
    parser_p = subparsers.add_parser(SUBSUBPARSER_NAME_P, help='Precision')
    parser_add_file_support(parser_p)
    parser_micro_support(parser_p)
    parser_p.set_defaults(func=parse)
    

def create_parser(subparsers):
    '''
    Setup a command line parser for this module's metric.
    '''
    parser = subparsers.add_parser('wpr',
                                   help=OUTPUT_NAME)
    
    subsubparsers = parser.add_subparsers(title='submetric', 
                                       description='Calculates a specified '+\
                                            'information retrieval (IR) '+\
                                            'metric from values provided by '+\
                                            'WinPR',
                                       help='Available IR metrics',
                                       dest='subsubparser_name')
    create_submetric_parser(subsubparsers)

