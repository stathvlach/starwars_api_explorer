How to run the application:

1. Create a new python venv:

python -m venv virtualenv-stathvlach

2. Change directory to virtual env directory

cd virtualenv-stathvlach

3. Clone the git repo in the virtual env directory

git clone https://github.com/stathvlach/starwars_api_explorer.git

4. Activate the venv

.\Scripts\activate

5. Change directory to repo directory

cd .\starwars_api_explorer

6. Run pip on requirements.txt

pip install -r requirements.txt

7. Run the application

python main.py search 'luke'

To test the visuals please run:

python main.py visuals --show

Select a search term to pop up the details.



