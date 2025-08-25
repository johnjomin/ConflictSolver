import os
import json
from z3 import *

# Function to load policies from JSON files in a specified directory
def load_policies(directory):
    policies = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                policy = json.load(file)
                policies.append(policy)
    return policies

def parse_conditions(policy):
    try:
        z3_vars = {}
        
        # Create Z3 variables for each parameter dynamically
        for param_key, param_data in policy["conditions"].items():
            if param_key.startswith("parameter") and "targets" in param_data and "name" in param_data:
                var_name = f"{param_data['targets']}.{param_data['name']}"
                z3_vars[var_name] = Real(var_name)
        
        exprs = []
        logic = policy["conditions"]["logic"]

        for param_key, param_data in policy["conditions"].items():
            if param_key.startswith("parameter"):
                var_name = f"{param_data['targets']}.{param_data['name']}"
                value = float(param_data['value1'])

                # Apply conditions dynamically based on logic string
                if f"{param_key}.targets.name > {param_key}.value1" in logic:
                    exprs.append(z3_vars[var_name] > value)
                elif f"{param_key}.targets.name <= {param_key}.value1" in logic:
                    exprs.append(z3_vars[var_name] <= value)
                elif f"{param_key}.targets.name < {param_key}.value1" in logic:
                    exprs.append(z3_vars[var_name] < value)
                elif f"{param_key}.targets.name >= {param_key}.value1" in logic:
                    exprs.append(z3_vars[var_name] >= value)

        # Parse top-level logic operators explicitly
        if "AND" in logic and "OR" not in logic:
            return And(*exprs)
        elif "OR" in logic and "AND" not in logic:
            return Or(*exprs)
        else:
            # Handle mixed AND/OR as nested expressions
            and_parts = logic.split(" AND ")
            nested_exprs = []
            for part in and_parts:
                if "OR" in part:
                    or_conditions = part.split(" OR ")
                    nested_exprs.append(Or(*[expr for expr in exprs if any(cond in str(expr) for cond in or_conditions)]))
                else:
                    nested_exprs.append(And(*[expr for expr in exprs if part in str(expr)]))
            return And(*nested_exprs)
    except Exception as e:
        print(f"Error parsing conditions for policy '{policy['name']}': {e}")
        return None

def check_policy_conflict(policy1, policy2):
    try:
        s = Solver()
        
        cond1 = parse_conditions(policy1)
        cond2 = parse_conditions(policy2)

        # Check if conditions are parsed correctly (not None)
        if cond1 is not None and cond2 is not None:
            # Solve for the negation of the combination to check for true conflict
            s.add(cond1)
            s.add(cond2)
            result = s.check()
            if result == unsat:  # unsat indicates a direct conflict
                print(f"Conflict Detected: {policy1['name']} and {policy2['name']}")
                return True
            else:
                return False
        else:
            print(f"Skipping conflict check for {policy1['name']} and {policy2['name']} due to parsing error.")
            return False
    except Exception as e:
        print(f"Error checking conflict between '{policy1['name']}' and '{policy2['name']}': {e}")
        return False


# Main function to load policies and detect conflicts
def main():
    directory = './Policies/'  # Directory containing JSON files with policies
    policies = load_policies(directory)
    
    if not policies:
        print("No policies found.")
        return
    
    conflicts = []
    for i in range(len(policies)):
        for j in range(i + 1, len(policies)):
            if check_policy_conflict(policies[i], policies[j]):
                conflicts.append((policies[i]["name"], policies[j]["name"]))
    
    if conflicts:
        print("Conflicts detected:")
        for conflict in conflicts:
            print(f"{conflict[0]} and {conflict[1]}")
    else:
        print("No conflicts detected.")

if __name__ == "__main__":
    main()
