import os
import sqlite3
import requests
import argparse
from datetime import datetime
import json

import tkinter as tk
from tkinter import ttk

# Application settings

BASE_DIR = os.getcwd()

SQL_DIR = os.path.join(BASE_DIR, 'sql')
SQL_SWAPI_ATTRIBUTES_DDL_SCRIPT = os.path.join(SQL_DIR, 'tbl_dico_swapi_attributes_ddl.sql')
SQL_SWAPI_ATTRIBUTES_DML_SCRIPT = os.path.join(SQL_DIR, 'tbl_dico_swapi_attributes_dml.sql')
SQL_SWAPI_CACHE_DDL_SCRIPT = os.path.join(SQL_DIR, 'tbl_swapi_cache_ddl.sql')

SQLITE_DB = os.path.join(BASE_DIR, 'starwars.db')
SQLITE_MASTER_TABLE = 'sqlite_master'
SWAPI_ATTRIBUTES_TABLE = 'dico_swapi_attributes'
SWAPI_CACHE_TABLE = 'swapi_cache'

SWAPI_ROOT_URL = "https://www.swapi.tech/api"
HTTP_RESPONSE_OK = 200

earth_orbital_period = 365.26
earth_rotational_period = 24.0

##########################################################
##  Functions to perform low-level database operations  ##
##########################################################
def sql_execute_dql(query):

    if query is None:
        return None;
        
    if len(query) <= 0:
        return None
    
    records = None

    try:
        with sqlite3.connect(SQLITE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()

    except sqlite3.Error as e:
        print(e)
        return False
    finally:
        if records is not None:
            if len(records) > 0:
                return records
        else:
            return None


def sql_execute_dml(query):
    
    if query is None:
        return None;
        
    if len(query) <= 0:
        return None
    
    records_affected = 0
    try:
        with sqlite3.connect(SQLITE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            records_affected = cursor.rowcount
            cursor.close()

            conn.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        return records_affected


def sql_table_exist(table_name):
    
    if table_name is None:
        return False
    
    if len(table_name) <= 0:
        return False

    res = sql_execute_dql("SELECT count(name) FROM " + SQLITE_MASTER_TABLE + " WHERE type='table' AND name='" + table_name + "';")

    if res is not None:
        if res[0][0] == 1:
            return True
    return False


def sql_init_database():

    if not sql_table_exist(SWAPI_ATTRIBUTES_TABLE):

            cursor = None

            try:
                with sqlite3.connect(SQLITE_DB) as conn:

                    cursor = conn.cursor()

                    with open(SQL_SWAPI_ATTRIBUTES_DDL_SCRIPT) as file:
                        sql_script = file.read()
                        cursor.executescript(sql_script)

                    with open(SQL_SWAPI_ATTRIBUTES_DML_SCRIPT) as file:
                        sql_script = file.read()
                        cursor.executescript(sql_script)

            except sqlite3.Error as e:
                print(e)
            finally:
                if cursor:
                    cursor.close()

    if not sql_table_exist(SWAPI_CACHE_TABLE):

        cursor = None

        try:
            with sqlite3.connect(SQLITE_DB) as conn:

                cursor = conn.cursor()

                with open(SQL_SWAPI_CACHE_DDL_SCRIPT) as file:
                    sql_script = file.read()
                    cursor.executescript(sql_script)

        except sqlite3.Error as e:
            print(e)
        finally:
            if cursor:
                cursor.close()
        
    return None


################################################################
##  Functions to collect and presend data from Star Wars API  ##
################################################################

def swapi_get_characters(name_pattern, character_attrs, planet_attrs):

    if name_pattern is None:
        return None
    
    if len(name_pattern) <= 0:
        return None
    
    people_url = None

    response = requests.get(SWAPI_ROOT_URL)

    if response.status_code == HTTP_RESPONSE_OK:
        people_url = response.json()['result']['people']
    
    if people_url is not None:
        response = requests.get(people_url + '?name=' + name_pattern)

        if response.status_code == HTTP_RESPONSE_OK:

            characters = response.json()['result']

            characters_f = []
   
            for character in characters:

                attr_f = {'id': character['uid']}
                for attr in character_attrs:
                    attr_f[attr] = character['properties'][attr]

                # Get data for character's homeworld
                response = requests.get(attr_f['homeworld'])

                if response.status_code == HTTP_RESPONSE_OK:
                    planet = response.json()['result']

                    attr_f['homeworld'] = {'id': planet['uid']}
                    for attr in planet_attrs:
                        attr_f['homeworld'][attr] = planet['properties'][attr]

                    if attr_f['homeworld']['orbital_period'] != 'unknown':
                        attr_f['homeworld']['to_earth_years'] = float(attr_f['homeworld']['orbital_period'])/earth_orbital_period
                    else:
                        attr_f['homeworld']['to_earth_years'] = 'unknown'

                    if attr_f['homeworld']['rotation_period'] != 'unknown':
                        attr_f['homeworld']['to_earth_days'] = float(attr_f['homeworld']['rotation_period'])/earth_rotational_period
                    else:
                        attr_f['homeworld']['to_earth_days'] = 'unknown'

                characters_f.append(attr_f)

            if len(characters_f) > 0:
                return characters_f
    
    return None


def get_character_attr_labels():

    attr_labels = None

    records = sql_execute_dql("SELECT DISTINCT API_ATTRIBUTE, LABEL FROM " + SWAPI_ATTRIBUTES_TABLE + " WHERE API_ATTRIBUTE IS NOT NULL AND API_KEY = 'people';")
    if len(records) > 0:
        attr_labels = {}
        for record in records:
            attr_labels[record[0]] = record[1]
    
    return attr_labels


def get_planets_attr_labels():

    attr_labels = None

    records = sql_execute_dql("SELECT DISTINCT API_ATTRIBUTE, LABEL FROM " + SWAPI_ATTRIBUTES_TABLE + " WHERE API_ATTRIBUTE IS NOT NULL AND API_KEY = 'planets';")
    if len(records) > 0:
        attr_labels = {}
        for record in records:
            attr_labels[record[0]] = record[1]
    
    return attr_labels


def pretty_print_character(character, character_attrs):

    fmt_output = ""
    for attr in character_attrs:
        if attr == 'homeworld': continue 

        if character[attr] is not None:
            fmt_output = fmt_output + "\n" + character_attrs[attr] + ':' + str(character[attr])
    
    return fmt_output


def pretty_print_homeworld_info(character, planet_attrs):
    
    p = "\n\nHomeworld"
    p = p + "\n----------------"
    p = p + "\n" + planet_attrs['name'] + ':' + character['homeworld']['name']
    p = p + "\n" + planet_attrs['population'] + ':' + character['homeworld']['population']
    p = p + "\n"

    if character['homeworld']['to_earth_years'] != 'unknown' and character['homeworld']['to_earth_days'] != 'unknown':
        p = p +  "\nOn " + character['homeworld']['name'] + ", 1 year on earth is %0.2f years and 1 day  %0.2f days" % (character['homeworld']['to_earth_years'], character['homeworld']['to_earth_days'])
    else:
        p = p +  "\nThe force is not strong within you: Unknown homeworld"

    return p


############################################
##  Functions to manage the cache memory  ##
############################################
def cache_is_search_saved(search_term):

    if search_term is None or len(search_term) <= 0:
        return None
    
    res = sql_execute_dql("SELECT count(*) FROM " + SWAPI_CACHE_TABLE +" WHERE PROMPT_SEARCH_TERMS = '" + search_term +"';")
    
    if res is not None:
        if res[0][0] > 0:
            return True
    
    return False


def cache_save_search(search_term, search_results):

    q = "INSERT INTO " + SWAPI_CACHE_TABLE + " (PROMPT_SEARCH_TERMS, CACHE_TIMESTAMP, RESULTS_JSON) VALUES ("
    q = q + "'" + search_term + "', "
    q = q + "'" + datetime.now().strftime("%Y-%m-%d_%H~%M~%S.000%f") + "', "
    q = q + "'" + json.dumps(search_results) + "');"

    if sql_execute_dml(q) > 0:
        return True
    else: 
        return False


def cache_load_search(search_term):

    if search_term is None or len(search_term) <= 0:
        return None

    cached_search = sql_execute_dql("SELECT CACHE_TIMESTAMP, RESULTS_JSON FROM swapi_cache WHERE PROMPT_SEARCH_TERMS = '" + search_term + "' GROUP BY PROMPT_SEARCH_TERMS HAVING CACHE_ID = max(CACHE_ID);")

    if cached_search is not None:
        if len(cached_search[0]) > 1:
            if len(cached_search[0][0]) > 0 and len(cached_search[0][1]) > 0:
                return (cached_search[0][0], json.loads(cached_search[0][1]))
    return None

def cache_load_search_by_term_and_date(term, date):

    if term is None or len(term) <= 0:
        return None
    
    if date is None or len(date) <= 0:
        return None
    
    records = sql_execute_dql("SELECT RESULTS_JSON FROM swapi_cache WHERE PROMPT_SEARCH_TERMS ='" + term + "' and CACHE_TIMESTAMP like '" + date + "%';")

    if records is not None:
        return json.loads(records[0][0])
    
    return None

def cache_load_all():

    records = sql_execute_dql("SELECT DISTINCT PROMPT_SEARCH_TERMS, CACHE_TIMESTAMP FROM " + SWAPI_CACHE_TABLE + ";")

    records_f = []
    if records is not None:
        for record in records:
            records_f.append((record[0], record[1]))
        
        if len(records_f) > 0:
            return records_f
    return None


def cache_clean():

    if sql_execute_dml("DELETE FROM swapi_cache;") > 0:
        return True
    else:
        return False

###############################
##  GUI even handlers        ##
###############################
def tk_search_selected(event):

    sel_search_term = left_tree.item(left_tree.selection()[0], option="text")
    sel_search_date = left_tree.item(left_tree.selection()[0], option="value")[0]

    sel_search_results = cache_load_search_by_term_and_date(sel_search_term, sel_search_date)

    if sel_search_results is not None:
        for item in right_tree.get_children():
            right_tree.delete(item)

        for sel_result in sel_search_results:
            right_tree.insert("", tk.END, text=sel_result['name'], values=(sel_result['height'], sel_result['mass'], sel_result['birth_year'], sel_result['homeworld']['name']))
 
        right_tree.pack()
    return


####################################################
##  Handler functions for command line arguments  ##
####################################################
def command_handler_search(args):

    characters = None
    is_cached_msg = ''
    character_attrs = get_character_attr_labels()
    planets_attrs = get_planets_attr_labels()

    if cache_is_search_saved(args.search_query):
        
        res = cache_load_search(args.search_query)

        characters = res[1]
        is_cached_msg = "\n\ncached: " + (str(res[0]).replace("_", " ").replace("~", ":"))[:-3]

    else:
        characters = swapi_get_characters(args.search_query, character_attrs, planets_attrs)

        if characters is None:
            print("The force is not strong within you ")
            return None
        
        cache_save_search(args.search_query, characters)

    for character in characters:

        print(pretty_print_character(character, character_attrs))

        if args.world:
            print(pretty_print_homeworld_info(character, planets_attrs))

    if len(is_cached_msg) > 0:
        print(is_cached_msg)

    return None


def command_handler_cache(args):

    if args.clean:
        if cache_clean():
            print('removed cache')

    return None

def command_handler_visuals(args):

    search_cache = cache_load_all()

    if search_cache is not None:
        if len(search_cache) > 0:

            root = tk.Tk()
            root.title("Star Wars API cache viewer")

            global left_tree
            left_tree = ttk.Treeview(root, columns=('search_date'), selectmode=tk.BROWSE)

            left_tree.tag_bind("tag_search_selected", "<<TreeviewSelect>>", tk_search_selected)

            left_tree.heading("#0", text="Search Term")
            left_tree.heading("search_date", text="Search Date")           

            for search in search_cache:
                item = left_tree.insert("", tk.END, text=search[0], values=(search[1].replace(" ", "_")[:-3]), tags=("tag_search_selected"))


            left_tree.pack()

            global right_tree
            right_tree = ttk.Treeview(root, columns=('height', 'mass', 'birth_year', 'homeworld'), selectmode=tk.BROWSE)

            right_tree.heading("#0", text="Name")
            right_tree.heading("height", text="Height")
            right_tree.heading("mass", text="Mass")
            right_tree.heading("birth_year", text="Birth Year")
            right_tree.heading("homeworld", text="Homeworld") 

            root.mainloop()          

    return None


###############################
##  Application Entry Point  ##
###############################

def main():

    sql_init_database()
        
    parser = argparse.ArgumentParser(
                prog='main',
                description='Explore Star Wars API (https://swapi.dev/)')
    
    subparsers = parser.add_subparsers(required=True)

    parser_search = subparsers.add_parser('search')
    search_group = parser_search.add_argument_group('Search for a Star Wars character')
    search_group.add_argument('search_query', help='Provide a character name or name pattern to search')
    search_group.add_argument('--world', default=False, action='store_true', help='Show additional info for the character(s) world(s)')
    parser_search.set_defaults(func=command_handler_search)

    parser_cache = subparsers.add_parser('cache')
    cache_group = parser_cache.add_argument_group('Manage the cache')
    cache_group.add_argument('--clean', default=False, action='store_true')
    parser_cache.set_defaults(func=command_handler_cache)

    parser_visuals = subparsers.add_parser('visuals')
    visuals_group = parser_visuals.add_argument_group('Show visual interface')
    visuals_group.add_argument('--show', default=False, action='store_true', help='Clear cache')
    parser_visuals.set_defaults(func=command_handler_visuals)

    args = None
    try:
        args = parser.parse_args()
        
    except Exception as e:
            print('Not sufficient arguments provided')
    finally:
        if args is not None:
            args.func(args)

    return True

###########################
##  Run the application  ##
###########################
if __name__ == '__main__':
    main()