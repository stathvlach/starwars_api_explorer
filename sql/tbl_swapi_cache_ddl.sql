CREATE TABLE IF NOT EXISTS swapi_cache
(
	CACHE_ID INTEGER PRIMARY KEY,
	PROMPT_SEARCH_TERMS TEXT,
	CACHE_TIMESTAMP DATETIME,
	RESULTS_JSON
);