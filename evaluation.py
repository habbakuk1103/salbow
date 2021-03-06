import click
from IPython import embed
import numpy as np
import os
from src.datasets import Dataset
from config import PATH_OUTPUT


from src import extract_raw_features
from src import compute_assignments

from src import load_targets, load_queries, save_sparse_csr, load_sparse_csr
from src import aqe


@click.command()
@click.option( '--dataset', default='instre', help='Selected dataset for extraction' )
@click.option( '--layer', default='conv5_1', help='layer from vgg16' )
@click.option( '--max_dim', default=340, help='Max dimension of images' )
@click.option( '--weighting', default=None, help='Spatial weighting scheme' )
@click.option( '--global_search', is_flag=True, help='Global Search for queries' )
@click.option( '--query_expansion', is_flag=True, help='Apply Average Query Expansion' )



def main(dataset, layer, max_dim, weighting, global_search, query_expansion):

    # init dataset information
    ds = Dataset( dataset, mask=weighting )

    # check if l2weighting
    if weighting == 'l2norm':
        # check that raw features exist
        path_raw_features = extract_raw_features( ds, PATH_OUTPUT, layer, max_dim, mode='keyframes' )

    # path to inv file
    path_file_keyframes = os.path.join( PATH_OUTPUT, 'inv_files', dataset, str(weighting), layer, str(max_dim) )
    # check if inverted file has been computed
    if os.path.exists( os.path.join( path_file_keyframes,'keyframes.npz') ):
        # load sparse matrix
        bow_targets = load_sparse_csr( os.path.join( path_file_keyframes,'keyframes') )
    else:
        # check assignments have been computed
        path_assignments = compute_assignments( ds, PATH_OUTPUT, layer, max_dim, mode='keyframes',  interpolate=2  )
        # build sparse matrix
        bow_targets = load_targets( ds, path_assignments, mask=weighting)

        # make output file
        if not os.path.exists( os.path.join( PATH_OUTPUT, 'inv_files', dataset, str(weighting), layer, str(max_dim) )):
            os.makedirs( os.path.join( PATH_OUTPUT, 'inv_files', dataset, str(weighting), layer, str(max_dim) ))
        # save to disk
        save_sparse_csr(os.path.join( path_file_keyframes,'keyframes'), bow_targets)

    # encode queries
    path_assignments_queries = compute_assignments( ds, PATH_OUTPUT, layer, max_dim, mode='queries', interpolate=2 )
    if not global_search:
        bow_queries = load_queries( ds, path_assignments_queries, mode='crop' )
    else:
        bow_queries = load_queries( ds, path_assignments_queries, mode='global' )

    aps, ranks = ds.evaluate(queries=bow_queries, targets=bow_targets)
    print "mAP = {}".format(np.mean(aps))

    if query_expansion:
        new_query = aqe( bow_targets, bow_queries, ranks )
        aps_QE, _ = ds.evaluate(queries=new_query, targets=bow_targets)
        print "+QE mAP = {}".format(np.mean(aps_QE))




if __name__ == '__main__':
    main()
