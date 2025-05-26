
from flask import Flask, render_template, request
import math

app = Flask(__name__)

def calculate_saturation_pressure(temp_celsius):
    """Calculate saturation pressure using Magnus formula for psychrometric calculations"""
    # Magnus formula for saturation vapor pressure over water
    # More accurate for psychrometric applications
    # Formula: P_sat = 0.61078 * exp(17.27 * T / (T + 237.3))
    # Where T is in Celsius and P_sat is in kPa
    
    p_sat_kpa = 0.61078 * math.exp(17.27 * temp_celsius / (temp_celsius + 237.3))
    
    return p_sat_kpa

def calculate_moisture_content(temp_out, rh_percent, temp_adp, temp_supply):
    """Calculate moisture content of supply air"""
    # Constants
    P_atm = 101.325  # kPa
    
    # Step 1: Calculate saturation pressure at outside temperature
    P_sat_out = calculate_saturation_pressure(temp_out)
    
    # Step 2: Calculate vapor pressure of outside air
    RH = rh_percent / 100.0  # Convert percentage to decimal
    P_vapor = RH * P_sat_out
    
    # Step 3: Calculate humidity ratio of outside air
    w_out = 0.622 * P_vapor / (P_atm - P_vapor)
    
    # Step 4: Calculate saturation pressure at ADP
    P_sat_adp = calculate_saturation_pressure(temp_adp)
    
    # Step 5: Calculate humidity ratio at ADP (saturated condition)
    w_adp = 0.622 * P_sat_adp / (P_atm - P_sat_adp)
    
    # Step 6: Linear interpolation for supply air condition
    x = (temp_supply - temp_adp) / (temp_out - temp_adp)
    w_supply = w_adp + x * (w_out - w_adp)
    
    # Create detailed calculation steps
    steps = {
        'P_atm': P_atm,
        'P_sat_out': P_sat_out,
        'RH_decimal': RH,
        'P_vapor': P_vapor,
        'P_sat_adp': P_sat_adp,
        'x_factor': x,
        'temp_out': temp_out,
        'temp_adp': temp_adp,
        'temp_supply': temp_supply,
        'rh_percent': rh_percent
    }
    
    return w_out, w_adp, w_supply, steps

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            # Get input values
            temp_out = float(request.form['temp_out'])
            rh_percent = float(request.form['rh_percent'])
            temp_adp = float(request.form['temp_adp'])
            temp_supply = float(request.form['temp_supply'])
            
            # Validate inputs
            if not (0 <= rh_percent <= 100):
                raise ValueError("Relative humidity must be between 0 and 100%")
            
            if temp_adp > temp_out:
                raise ValueError("ADP temperature cannot be higher than outside temperature")
            
            if not (temp_adp <= temp_supply <= temp_out):
                raise ValueError("Supply temperature must be between ADP and outside temperature")
            
            # Calculate moisture contents
            w_out, w_adp, w_supply, steps = calculate_moisture_content(temp_out, rh_percent, temp_adp, temp_supply)
            
            return render_template('index.html', 
                                 w_out=round(w_out, 6),
                                 w_adp=round(w_adp, 6),
                                 w_supply=round(w_supply, 6),
                                 temp_out=temp_out,
                                 rh_percent=rh_percent,
                                 temp_adp=temp_adp,
                                 temp_supply=temp_supply,
                                 steps=steps)
        
        except ValueError as e:
            return render_template('index.html', error=str(e))
        except Exception as e:
            return render_template('index.html', error="Calculation error: " + str(e))
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
