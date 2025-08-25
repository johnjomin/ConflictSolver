policy1 = {
    "policy_id": "Policy1",
    "metadata": {
        "priority": 1,
        "enabled": True,
        "requires_approval": True,
        "created_at": "2024-10-07",
        "updated_at": "2024-10-07"
    },
    "conditions": {
        "logic": "AND",
        "expressions": [
            {
                "logic": "OR",
                "conditions": [
                    {
                        "parameter": {"target": "Device", "name": "Bandwidth", "unit": "Mbps"},
                        "operator": ">",
                        "value": "5"
                    },
                    {
                        "parameter": {"target": "Device", "name": "Temperature", "unit": "Celsius"},
                        "operator": "<",
                        "value": "30"
                    }
                ]
            },
            {
                "parameter": {"target": "Device", "name": "FanStatus"},
                "operator": "==",
                "value": "ON"
            }
        ]
    },
    "actions": [
        {
            "parameter": {"target": "Device", "name": "FanControl"},
            "value": "ON",
            "execution_conditions": {
                "logic": "AND",
                "conditions": [
                    {
                        "parameter": {"target": "Device", "name": "Temperature"},
                        "operator": ">=",
                        "value": "25"
                    }
                ]
            }
        }
    ],
    "conflict_resolution": {
        "resolution_strategy": "priority",
        "conflict_score": 0.75
    }
}
policy2 = {
    "policy_id": "Policy2",
    "metadata": {
        "priority": 2,
        "enabled": True,
        "requires_approval": False,
        "created_at": "2024-10-07",
        "updated_at": "2024-10-07"
    },
    "conditions": {
        "logic": "AND",
        "expressions": [
            {
                "parameter": {"target": "Device", "name": "Bandwidth", "unit": "Mbps"},
                "operator": "<=",
                "value": "5"
            },
            {
                "parameter": {"target": "Device", "name": "Temperature"},
                "operator": ">=",
                "value": "25"
            }
        ]
    },
    "actions": [
        {
            "parameter": {"target": "Device", "name": "FanControl"},
            "value": "OFF"
        }
    ],
    "conflict_resolution": {
        "resolution_strategy": "latest_version",
        "conflict_score": 0.85
    }
}
policy3 = {
    "policy_id": "Policy3",
    "metadata": {
        "priority": 3,
        "enabled": True,
        "requires_approval": True,
        "created_at": "2024-10-07",
        "updated_at": "2024-10-07"
    },
    "conditions": {
        "logic": "OR",
        "expressions": [
            {
                "parameter": {"target": "Device", "name": "Humidity", "unit": "%"},
                "operator": "<",
                "value": "40"
            },
            {
                "parameter": {"target": "Device", "name": "Pressure", "unit": "kPa"},
                "operator": ">",
                "value": "101.3"
            }
        ]
    },
    "actions": [
        {
            "parameter": {"target": "Device", "name": "CoolingSystem"},
            "value": "ON"
        }
    ],
    "conflict_resolution": {
        "resolution_strategy": "priority",
        "conflict_score": 0.60
    }
}
policy4 = {
    "policy_id": "Policy4",
    "metadata": {
        "priority": 4,
        "enabled": True,
        "requires_approval": False,
        "created_at": "2024-10-07",
        "updated_at": "2024-10-07"
    },
    "conditions": {
        "logic": "AND",
        "expressions": [
            {
                "parameter": {"target": "Device", "name": "Temperature"},
                "operator": "<",
                "value": "25"
            },
            {
                "parameter": {"target": "Device", "name": "FanStatus"},
                "operator": "!=",
                "value": "OFF"
            }
        ]
    },
    "actions": [
        {
            "parameter": {"target": "Device", "name": "CoolingSystem"},
            "value": "OFF"
        }
    ],
    "conflict_resolution": {
        "resolution_strategy": "most_severe",
        "conflict_score": 0.65
    }
}
policy5 = {
    "policy_id": "Policy5",
    "metadata": {
        "priority": 5,
        "enabled": True,
        "requires_approval": True,
        "created_at": "2024-10-07",
        "updated_at": "2024-10-07"
    },
    "conditions": {
        "logic": "AND",
        "expressions": [
            {
                "parameter": {"target": "Device", "name": "Humidity", "unit": "%"},
                "operator": ">",
                "value": "60"
            },
            {
                "parameter": {"target": "Device", "name": "Pressure", "unit": "kPa"},
                "operator": "<=",
                "value": "100"
            }
        ]
    },
    "actions": [
        {
            "parameter": {"target": "Device", "name": "CoolingSystem"},
            "value": "OFF"
        }
    ],
    "conflict_resolution": {
        "resolution_strategy": "priority",
        "conflict_score": 0.55
    }
}

from z3 import *

# Modified function to dynamically create Z3 variables based on parameter type
def create_z3_variable(parameter, value):
    var_name = f"{parameter['target']}.{parameter['name']}"
    if isinstance(value, (int, float)) or value.replace('.', '', 1).isdigit():
        return Real(var_name)
    else:
        return String(var_name)

# Function to parse conditions and handle both numeric and string types
def parse_conditions(conditions):
    expressions = []
    for expression in conditions["expressions"]:
        if "conditions" in expression:  # Nested logic
            sub_expr = parse_conditions({"logic": expression["logic"], "expressions": expression["conditions"]})
            expressions.append(sub_expr)
        else:
            parameter = expression["parameter"]
            operator = expression["operator"]
            value = expression["value"]
            
            # Determine if the value is numeric or a string
            if isinstance(value, str) and not value.replace('.', '', 1).isdigit():
                var = create_z3_variable(parameter, value)
                if operator == "==":
                    expressions.append(var == value)
                elif operator == "!=":
                    expressions.append(var != value)
            else:
                var = create_z3_variable(parameter, float(value))
                numeric_value = float(value)
                
                # Map operator to Z3
                if operator == ">":
                    expressions.append(var > numeric_value)
                elif operator == "<":
                    expressions.append(var < numeric_value)
                elif operator == "==":
                    expressions.append(var == numeric_value)
                elif operator == "!=":
                    expressions.append(var != numeric_value)
                elif operator == ">=":
                    expressions.append(var >= numeric_value)
                elif operator == "<=":
                    expressions.append(var <= numeric_value)

    # Combine expressions based on the top-level logic operator
    if conditions["logic"] == "AND":
        return And(*expressions)
    elif conditions["logic"] == "OR":
        return Or(*expressions)

# Function to check for conflicts between two policies
def check_policy_conflict(policy1, policy2):
    try:
        s = Solver()
        
        # Parse conditions for both policies
        cond1 = parse_conditions(policy1["conditions"])
        cond2 = parse_conditions(policy2["conditions"])
        
        # Only proceed if both conditions are valid
        if cond1 is not None and cond2 is not None:
            s.add(cond1)
            s.add(cond2)
            result = s.check()
            
            # Print only if there is a conflict detected
            if result == unsat:
                return True
            return False
        else:
            # Handle cases where conditions may not have parsed correctly
            print(f"Skipping conflict check for {policy1['policy_id']} and {policy2['policy_id']} due to parsing error.")
            return False
    except Exception as e:
        print(f"Error checking conflict between '{policy1['policy_id']}' and '{policy2['policy_id']}': {e}")
        return False




policies = [policy1, policy2, policy3, policy4, policy5]

# Main function to detect conflicts among policies
def main():
    conflicts = []
    for i in range(len(policies)):
        for j in range(i + 1, len(policies)):
            if check_policy_conflict(policies[i], policies[j]):
                conflicts.append((policies[i]["policy_id"], policies[j]["policy_id"]))
    
    # Print a summary of conflicts at the end
    if conflicts:
        for conflict in conflicts:
            print(f"Conflicts Detected: {conflict[0]} and {conflict[1]}")
    else:
        print("No conflicts detected.")

if __name__ == "__main__":
    main()


