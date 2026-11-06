import requests
import json
from flask import Flask, render_template, flash, request, redirect, url_for
from redis import Redis
from helper import validate_email, validate_password, load_secret_key

# Initialize Flask app
app = Flask(__name__)
app.secret_key = load_secret_key() 

# Initialize Redis instance
redis = Redis(host='redis', port=6379)

API_BASE_URL = 'https://wepgen.paxtonpatronas.com/api'

def check_access_token():
    try:
        access_token = redis.get("access_token").decode("utf-8")
        return access_token
    except:
        flash("You are not currently logged in.")
        return "bad_token"

def api_request(method, endpoint, access_token=None, content_type=None, **kwargs):

    headers = {'accept': '*/*'}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    if content_type:
        headers['Content-Type'] = content_type
    return requests.request(method, API_BASE_URL + endpoint, headers=headers, **kwargs)

def flash_api_error(response, default_message):
    """Flash the API's error detail, or a default message if there isn't one."""
    try:
        flash(response.json()['detail'])
    except:
        flash(default_message)

@app.route('/', methods=['GET', 'POST'])
def main():
    return render_template('main.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == "POST":
        if request.form['password'] != request.form['confirm_password']:
            flash("Passwords do not match.")
            return redirect(url_for('main'))

        if not validate_password(request.form['password']):
            flash ("Password is not secure.")
            return redirect(url_for('main'))

        if not validate_email(request.form['email']):
            flash("Invalid email.")
            return redirect(url_for('main'))

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        json_data = {
            'name': username,
            'email': email,
            'password': password,
        }

        response = api_request('POST', '/json/register', json=json_data)

        if response.status_code != 200:
            flash_api_error(response, "Cannot register at this time.")
        else:
            flash("Account registered.")
        return redirect(url_for('main'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        payload = {
            "grant_type": "password",
            "username": username, 
            "password": password,
            "scope": "",
            "client_id": "string",
            "client_secret": "********",
        }

        response = api_request('POST', '/json/token', data=payload)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            if token_data:
                redis.set("access_token", access_token, ex=(60*20))
            flash("Logged in.")
        else:
            flash_api_error(response, "Cannot login at this time.")

    return render_template('main.html')

# Create operation for loadout
@app.route('/generate', methods=['POST'])
def generate_loadout():
    if request.method == "POST":
        # Info used for loadout algorithm
        tf_class = request.form['class']
        game_goal = request.form['game_goal']
        individual_goal = request.form['individual_goal']

        access_token = check_access_token()

        params = {
            'class_name': tf_class,
        }

        response = api_request('GET', '/weapons/search', access_token=access_token, params=params)
        data = response.json()

        # Base traits
        damage = 3
        utility = 3
        w_range = 3
        offense = 3
        defense = 3
        reliability = 3

        if game_goal == "Win":
            win = True
            fun = False
            # More reliable, less gimicky weapons
            reliability += 2
            utility -= 1

        if game_goal == "Fun":
            fun = True
            win = False
            # Perchance the weapon is less reliable
            reliability -= 1

        if game_goal == "Both":
            fun = True
            win = True
            # Just keep the stuff the same

        if individual_goal == "Team Player":
            # More utility/defense based weapons
            utility += 2
            defense += 2
            offense -= 1
            w_range += 1

        if individual_goal == "Top Frag":
            # Less utility, more damage and less range
            utility -= 1
            offense += 2
            defense -= 1
            w_range -= 1
            damage += 1

        potential_weapons = []

        def find_weapons(weapon_type):
            #print("Weapon: " + str(weapon_type['name']))
            weapon_traits = ['damage', 'utility', 'range', 'offense', 'defense', 'reliability']
            personal_traits = [damage, utility, w_range, offense, defense, reliability]
            trait_percentages = []
            for i in range(len(weapon_traits)):
                if weapon_type['traits'][weapon_traits[i]] ==  personal_traits[i]:
                    trait_percentages.append(1.0)
                elif weapon_type['traits'][weapon_traits[i]] >  personal_traits[i]:
                    trait_percentages.append(personal_traits[i] / weapon_type['traits'][weapon_traits[i]])
                else:
                    trait_percentages.append(weapon_type['traits'][weapon_traits[i]] / personal_traits[i])
            #print(weapon_type['name'] + "\'s damage: " + str(trait_percentages[0]))
            #print(weapon_type['name'] + "\'s utility: " + str(trait_percentages[1]))
            #print(weapon_type['name'] + "\'s range: " + str(trait_percentages[2]))
            #print(weapon_type['name'] + "\'s offense: " + str(trait_percentages[3]))
            #print(weapon_type['name'] + "\'s defense: " + str(trait_percentages[4]))
            #print(weapon_type['name'] + "\'s reliability: " + str(trait_percentages[5]))

            odds = sum(trait_percentages) / 6
            odds = [str(weapon_type['name']), odds]
            return odds

        def determine_best(odds_list):
            return max(odds_list, key=odds_list.get)

        odds_list = {}

        for weapon, characteristics in data["primary"].items():
            # Rebuild the dictionary that is passed into the weapon_odds function
            weapon_type = {}
            weapon_type[weapon] = characteristics
            weapon_odds = find_weapons(weapon_type[weapon])
            weapon_name, weapon_percentage = weapon_odds[0], weapon_odds[1]
            odds_list[weapon_name] = weapon_percentage

        primary = determine_best(odds_list)

        odds_list.clear()

        for weapon, characteristics in data["secondary"].items():
            # Rebuild the dictionary that is passed into the weapon_odds function
            weapon_type = {}
            weapon_type[weapon] = characteristics
            weapon_odds = find_weapons(weapon_type[weapon])
            weapon_name, weapon_percentage = weapon_odds[0], weapon_odds[1]
            odds_list[weapon_name] = weapon_percentage

        secondary = determine_best(odds_list)
        
        odds_list.clear()

        for weapon, characteristics in data["melee"].items():
            # Rebuild the dictionary that is passed into the weapon_odds function
            weapon_type = {}
            weapon_type[weapon] = characteristics
            weapon_odds = find_weapons(weapon_type[weapon])
            weapon_name, weapon_percentage = weapon_odds[0], weapon_odds[1]
            odds_list[weapon_name] = weapon_percentage

        melee = determine_best(odds_list)

        odds_list.clear()

        if tf_class == "Engineer":
            # This is the only PDA for Engineer
            pda = "Construction PDA"
        if tf_class == "Spy":
            for weapon, characteristics in data["pda"].items():
                # Rebuild the dictionary that is passed into the weapon_odds function
                weapon_type = {}
                weapon_type[weapon] = characteristics
                weapon_odds = find_weapons(weapon_type[weapon])
                weapon_name, weapon_percentage = weapon_odds[0], weapon_odds[1]
                odds_list[weapon_name] = weapon_percentage

            pda = determine_best(odds_list)

        json_data = {
            'preferences': {
                'win_fun_both': game_goal,
                'teamplayer_topfrag': individual_goal,
                'w_damage': damage,
                'w_utility': utility,
                'w_range': w_range,
                'w_offense': offense,
                'w_defense': defense,
                'w_reliability': reliability,
            },
            'loadout': {
                'l_class': tf_class,
                'l_primary': primary,
                'l_secondary': secondary,
                'l_melee': melee,
            }
        }
        # Add PDA if the class selected is Engineer or Spy
        if tf_class in ['Engineer', 'Spy']:
            json_data['loadout']['l_pda'] = pda

        response = api_request('POST', '/loadouts/loadout_create', access_token=access_token, json=json_data)

        if response.status_code != 200:
            flash_api_error(response, "Could not generate loadout at this time.")
            return redirect(url_for('main'))
        else:
            flash("Loadout generated.")

    return redirect(url_for('loadouts'))

# Read operation for loadouts
@app.route('/loadouts')
def loadouts():
    access_token = check_access_token() 
    if access_token == "bad_token":
        return redirect(url_for('main'))
    response = api_request('GET', '/loadouts/loadout_readall', access_token=access_token)
    try:
        loadout_data = response.json()
    except:
        flash("Could not read loadouts at this time.")
        return redirect(url_for('main'))

    return render_template('loadouts.html', loadout_data=loadout_data)

# Update operation for loadouts
@app.route('/edit_loadout/<int:loadout_id>', methods=['GET', 'POST'])
def edit_loadout(loadout_id):
    access_token = check_access_token() 
    if access_token == "bad_token":
        return redirect(url_for('main'))

    if request.method == "GET":
        # Read the individual loadout
        params = {
            'loadout': loadout_id,
        }

        response = api_request('GET', '/loadouts/loadout_read', access_token=access_token, params=params)

        loadout_data = response.json()

        # Read the weapons for class
        params = {
            'class_name': loadout_data[0]['class'],
        }

        response = api_request('GET', '/weapons/search', access_token=access_token, params=params)
        possible_weapons = response.json()

        return render_template('edit_loadout.html', loadout_data=loadout_data, possible_weapons=possible_weapons, loadout_id=loadout_id)

    # If it's a post method, a loadout is going to be updated
    if request.method == "POST":
        primary = request.form['primary_edit']
        secondary = request.form['secondary_edit']
        melee = request.form['melee_edit']
        pda = request.form['pda_edit'] if request.form['pda_edit'] != "nada" else None

        json_data = {
            'user_loadout_id': loadout_id,
            'l_primary': primary,
            'l_secondary': secondary,
            'l_melee': melee,
        }
        if pda:
            json_data['l_pda'] = pda

        response = api_request('POST', '/loadouts/loadout_update', access_token=access_token, json=json_data)

        if response.status_code != 200:
            flash_api_error(response, "Could not edit loadout at this time")
            return redirect(url_for('main'))
        else:
            flash("Loadout edited.")

        return redirect(url_for('loadouts')) 

# Delete operation for loadouts
@app.route('/delete_loadout', methods=['POST'])
def delete_loadout():
    if request.method == "POST":
        loadout_id = request.form['loadout_id']
        access_token = check_access_token() 
        if access_token == "bad_token":
            return redirect(url_for('main'))
        json_data = {
            'user_loadout_id': loadout_id,
        }

        response = api_request('POST', '/loadouts/loadout_delete', access_token=access_token, json=json_data)

        if response.status_code == 200:
            flash("Loadout deleted.")
        else:
            flash_api_error(response, "Could not delete loadout at this time.")
            return redirect(url_for('main'))

    return redirect(url_for('loadouts'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    access_token = check_access_token()
    if access_token == "bad_token":
        return redirect(url_for('main'))
    if request.method == "POST":
        response = api_request('POST', '/json/account_delete', access_token=access_token,
                               content_type='application/x-www-form-urlencoded')
        if response.status_code == 200:
            flash("Account deleted.")
            redis.delete("access_token")
        else:
            flash_api_error(response, "Could not delete account at this time.")

    return redirect(url_for('main'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
