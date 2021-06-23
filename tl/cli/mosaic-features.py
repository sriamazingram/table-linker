import sys
import argparse
import traceback
import tl.exceptions


def parser():
    return {
        'help': 'generates number of characters and tokens in a particular column'
    }


def add_arguments(parser):
    """
    Parse Arguments
    Args:
        parser: (argparse.ArgumentParser)

    """
    parser.add_argument('-c', '--column', action='store', type=str, dest='label_column', required=True,
                        default='kg_labels',
                        help='name of the column for which number of characters and tokens need to be calculated')

    parser.add_argument('--num-char', action='store_true', dest='num_char', required=False,
                        default=False,
                        help='if specified, computes number of characters in the column mentioned by the user')

    parser.add_argument('--num-tokens', action='store_true', dest='num_tokens', required=False,
                        default=False,
                        help='if specified, computes number of characters in the column mentioned by the user')

    parser.add_argument('input_file', nargs='?', type=argparse.FileType('r'), default=sys.stdin)


def run(**kwargs):
    from tl.features import mosaic_features
    import pandas as pd
    import time
    try:
        df = pd.read_csv(kwargs['input_file'], dtype=object)
        start = time.time()
        odf = mosaic_features.mosaic_features(kwargs['label_column'],
                                             kwargs['num_char'],
                                             kwargs['num_tokens'],
                                             df=df)
        end = time.time()
        if kwargs["logfile"]:
            with open(kwargs["logfile"],"a") as f:
                print(f'mosaic-features Time: {str(end-start)}s'
                      f' Input: {kwargs["input_file"]}',file=f)
        else:
            print(f'mosaic-features Time: {str(end-start)}s'
                  f' Input: {kwargs["input_file"]}',file=sys.stderr)
        odf.to_csv(sys.stdout, index=False)
    except:
        message = 'Command: mosaic-features\n'
        message += 'Error Message:  {}\n'.format(traceback.format_exc())
        raise tl.exceptions.TLException(message)
