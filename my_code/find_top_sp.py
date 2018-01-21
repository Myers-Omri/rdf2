from SPARQLWrapper import SPARQLWrapper, JSON
import os
import pickle
import sys
from threading import Thread
from Utils import *

DBPEDIA_URL_UP = "http://dbpedia.org/sparql"
DBPEDIA_URL = "http://tdk3.csf.technion.ac.il:8890/sparql"

def get_top_1_percent(i, top_s_dict,uri, f_limit = 200):
    sparql = SPARQLWrapper(DBPEDIA_URL)

    limit = 10000
    offset = i * limit
    s_f_limit = str(f_limit)

    slimit = str(limit)
    soffset = str(offset)
    query_text = ("""
    SELECT ?s(COUNT(*)AS ?scnt)
    WHERE
    {
        {
            SELECT DISTINCT ?s ?p
            WHERE
            {
                {
                    SELECT DISTINCT ?s
                    WHERE
                    {
                        ?s a <%s>.
                    } LIMIT %s
                    OFFSET %s
                }
                ?s ?p ?o.
                FILTER regex(?p, "^http://dbpedia.org/ontology/", "i")
            }
        }
    } GROUP BY ?s
    ORDER BY DESC(?scnt)
    LIMIT %s""" % (uri,slimit, soffset, s_f_limit))

    sparql.setQuery(query_text)
    sparql.setReturnFormat(JSON)
    results_inner = sparql.query().convert()
    all_dict = results_inner["results"]["bindings"]
    for inner_res in all_dict:
        s = inner_res["s"]["value"]
        cnt = inner_res["scnt"]["value"]
        if cnt>20:
            top_s_dict[s] = cnt
    if len(all_dict) > 10:
        return True
    return False


def get_f_limits(uri):
    cnt = 1
    sparql = SPARQLWrapper(DBPEDIA_URL)
    query_text = ("""
        SELECT (COUNT(*)AS ?scnt)
        WHERE
        {
            {
                SELECT DISTINCT ?s
                WHERE
                {
                    ?s a <%s>.
                }
            }
        }
        """ % (uri))

    sparql.setQuery(query_text)
    sparql.setReturnFormat(JSON)
    results_inner = sparql.query().convert()
    all_dict = results_inner["results"]["bindings"]
    for inner_res in all_dict:
        cnt = inner_res["scnt"]["value"]

    r = float(5000)/ float(cnt)

    l = r * 10000 if r < 0.5 else int(cnt)

    # just to make sure we dont miss anyone
    return int(l), int(cnt)



def get_all_top_of(uri , f_name, dir_name):

    i=0
    top_subjects = {}
    limits, maxs = get_f_limits(uri)
    flag = get_top_1_percent(i, top_subjects, uri, limits)
    while flag:
        i += 1
        flag = get_top_1_percent(i, top_subjects, uri, limits)

        # txt = "\b i progress:{} ".format(i)
        # sys.stdout.write(txt)
        # sys.stdout.write("\r")
        # sys.stdout.flush()
        if i>150 or i*1000>maxs:
            flag = False

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    s_dict_file = open("../results/" + dir_name + "/" + f_name, 'w')
    pickle.dump(top_subjects, s_dict_file)
    s_dict_file.close()
    #print "get top s  done for {}, i is:{}".format(f_name, i)



def get_all_p_dict(uri, dump_name,dir_name):
    sparql = SPARQLWrapper(DBPEDIA_URL)
    p_dict = {}


    query_text = ("""
            SELECT ?p (COUNT (?p) AS ?cnt)
            WHERE {
                    {
                    SELECT DISTINCT ?s ?p
                    WHERE {
                        ?s a <%s>;
                            ?p ?o.
                        ?o a ?t
                    FILTER regex(?p, "^http://dbpedia.org/ontology/", "i")
                }LIMIT 500000
            }
            }GROUP BY ?p
             ORDER BY DESC(?cnt)
             LIMIT 50
            """ % uri)
    sparql.setQuery(query_text)
    sparql.setReturnFormat(JSON)
    results_inner = sparql.query().convert()

    for inner_res in results_inner["results"]["bindings"]:
        p = inner_res["p"]["value"]
        cnt = inner_res["cnt"]["value"]
        p_dict[p] = cnt
    dir_name = "../results/" + dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    p_dict_file = open(dir_name + "/" + dump_name, 'w')
    pickle.dump(p_dict, p_dict_file)
    p_dict_file.close()
    #print "pdict done for: {}".format(dir_name)


def get_p_p_dict(uri, dump_name,dir_name):
    sparql = SPARQLWrapper(DBPEDIA_URL)
    p_dict = {}

    query_text = ("""
            SELECT ?p (COUNT (?p) AS ?cnt)
            WHERE {
                    {
                    SELECT DISTINCT ?s ?p
                    WHERE {
                        ?s a <%s>;
                            ?p ?o.
                        ?o a ?t
                    FILTER regex(?p, "^http://dbpedia.org/property/", "i")
                }LIMIT 500000
            }
            }GROUP BY ?p
             ORDER BY DESC(?cnt)
             LIMIT 50
            """ % uri)
    sparql.setQuery(query_text)
    sparql.setReturnFormat(JSON)
    results_inner = sparql.query().convert()

    for inner_res in results_inner["results"]["bindings"]:
        p = inner_res["p"]["value"]
        cnt = inner_res["cnt"]["value"]
        p_dict[p] = cnt

    dir_name = "../results/" + dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    p_dict_file = open(dir_name + "/" + dump_name, 'w')
    pickle.dump(p_dict, p_dict_file)
    p_dict_file.close()
    #print "pdict done for: {}".format(dir_name)


def get_ps(uri, s_name ):
    print "started: " +s_name
    subjects_fname = s_name + "_top.dump"
    pprop_fname = s_name + "_prop.dump"
    #pprop_fname_p = s_name + "_prop_p.dump"

    get_all_top_of(uri, subjects_fname, s_name)
    get_all_p_dict(uri, pprop_fname, s_name)
    #get_p_p_dict(uri, pprop_fname_p, s_name)

    print "finished: " + s_name



def get_best_prop_q(i, top_p_dict,uri = "http://dbpedia.org/ontology/Person", f_limit = 200):
    sparql = SPARQLWrapper(DBPEDIA_URL)

    limit = 100000
    offset = i * limit
    s_f_limit = str(f_limit)

    slimit = str(limit)
    soffset = str(offset)

    query_text = ("""
                SELECT ?p (COUNT (?p) AS ?cnt)
                WHERE {
                        {
                        SELECT DISTINCT ?s ?p
                        WHERE {
                            ?s a <%s>;
                                ?p ?o.
                            ?o a ?t
                        FILTER regex(?p, "^http://dbpedia.org/property/", "i")
                    }LIMIT %s
                    OFFSET %s
                }
                }GROUP BY ?p
                 ORDER BY DESC(?cnt)
                 LIMIT %s
                """ % (uri, slimit, soffset, s_f_limit))
    sparql.setQuery(query_text)
    sparql.setReturnFormat(JSON)
    results_inner = sparql.query().convert()

    t_count = 0
    for inner_res in results_inner["results"]["bindings"]:
        p = inner_res["p"]["value"]
        cnt = inner_res["cnt"]["value"]
        if p not in top_p_dict:
            top_p_dict[p] = 0
        top_p_dict[p] += int(cnt)
        t_count += int(cnt)
    return t_count>=200


def get_best_200_props(uri = "http://dbpedia.org/ontology/Person", dir_name="person"):

    p_dict={}
    top_num = 200
    iter_flag = True
    for i in range(25):
        if iter_flag:
            try:
                iter_flag = get_best_prop_q(i, p_dict, uri, top_num)
            except Exception as e:
                print "error in iter: " ,  i , " exception: ",e

    dump_name = dir_name + "_top_200_prop.dump"

    dir_name = "../results/" + dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    p_dict_file = open(dir_name + "/" + dump_name, 'w')
    pickle.dump(p_dict, p_dict_file)
    p_dict_file.close()


def get_best():
    p_dict_file = open("../results/person/person_top_200_prop.dump", 'r')
    p_dict = pickle.load(p_dict_file)
    p_dict_file.close()

    p_list = p_dict.items()
    sorted_by_second = sorted(p_list, key=lambda tup: tup[1])

    final_list = sorted_by_second[-20:]
    p_dict_best = dict(final_list)

    dir_name = "person"
    dump_name = dir_name + "_200_prop_for_ML.dump"
    dir_name = "../results/" + dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    p_dict_file = open(dir_name + "/" + dump_name, 'w')
    pickle.dump(p_dict_best, p_dict_file)
    p_dict_file.close()

if __name__ == '__main__':

    # for d in dictionariest:
    #     for s, uri in d.items():
    #         t = Thread(target=get_ps, args=(uri,s,))
    #         t.start()

    get_best()












