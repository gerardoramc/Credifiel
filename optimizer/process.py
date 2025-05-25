import pandas as pd

def mask_client_probabilities(df: pd.DataFrame, clients: dict) -> dict:
    """
    Keeps probabilities for a client's own bank and any INTERBANCARIO rows.
    All others are zeroed out.

    Parameters:
        df (pd.DataFrame): Must contain 'idEmisora', 'Nombre', and 'TipoEnvio'.
        clients (dict): {
            'client_1': {
                'probabilities': {idEmisora: probability, ...},
                'bank': 'BANK_NAME'
            },
            ...
        }

    Returns:
        dict: Same structure but with filtered probabilities.
    """
    # Bank to idEmisora mapping
    bank_to_ids = df.groupby("Nombre")["idEmisora"].apply(set).to_dict()

    # INTERBANCARIO idEmisora set
    interbancario_ids = set(df[df["TipoEnvio"] == "INTERBANCARIO"]["idEmisora"])

    for client_id, data in clients.items():
        client_bank = data["bank"]
        prob_dict = data["probabilities"]

        ids_from_bank = bank_to_ids.get(client_bank, set())
        ids_to_keep = ids_from_bank.union(interbancario_ids)

        # Keep only bank + interbancario ids
        data["probabilities"] = {
            em_id: prob if em_id in ids_to_keep else 0
            for em_id, prob in prob_dict.items()
        }

    return clients

def append_hit_costs(df: pd.DataFrame, clients: dict) -> dict:
    """
    Appends hit costs to the client dictionary.

    Parameters:
        df (pd.DataFrame): Must contain 'idEmisora', 'Costo_Hit_Miss', and 'Costo_Hit_Win'.
        clients (dict): {
            'client_1': {
                'probabilities': {idEmisora: probability, ...},
                'bank': 'BANK_NAME'
            },
            ...
        }

    Returns:
        dict: Same structure but with appended hit costs.
    """
    # Create a mapping of idEmisora to costs
    cost_mapping = df.set_index("idEmisora")[["Costo_Hit_Miss", "Costo_Hit_Win"]].to_dict(orient="index")
    # Get keys with no 0 values

    for client_id, data in clients.items():
        prob_dict = data["probabilities"]
        # Get keys with no 0 values
        keys_with_values = [k for k, v in prob_dict.items() if v != 0]
        data["hit_costs"] = {
            em_id: cost_mapping[em_id] if em_id in keys_with_values else None
            for em_id in prob_dict.keys()
        }
        # Remove keys with 0 values in data["hit_costs"]
        data["hit_costs"] = {k: v for k, v in data["hit_costs"].items() if v is not None}


    return clients  

def compute_profits_for_client(client_data):
    payment = client_data["payment"]
    probabilities = client_data["probabilities"]
    hit_costs = client_data.get("hit_costs", {})

    profits = {}

    for emisora_id, prob in probabilities.items():
        hit_cost = hit_costs.get(emisora_id, {})
        chm = hit_cost.get("Costo_Hit_Miss", 0)
        chw = hit_cost.get("Costo_Hit_Win", 0)

        if chm == chw:
            penalty = chm * 1
        else:
            penalty = chm * (1 - prob)

        profit = (payment * prob) + penalty
        profits[emisora_id] = profit

    return profits

def compute_penalties_for_client(client_data):
    # payment = client_data["payment"]  # Still available in case needed later
    probabilities = client_data["probabilities"]
    hit_costs = client_data.get("hit_costs", {})

    penalties = {}

    for emisora_id, prob in probabilities.items():
        hit_cost = hit_costs.get(emisora_id)

        # If there's no Costo_Hit_Miss info, assign None
        if not hit_cost or "Costo_Hit_Miss" not in hit_cost:
            penalties[emisora_id] = None
            continue

        chm = hit_cost["Costo_Hit_Miss"]
        chw = hit_cost.get("Costo_Hit_Win", 0)

        # Compute penalty
        if chm == chw:
            penalty = chm
        else:
            penalty = chm * (1 - prob)

        penalties[emisora_id] = penalty

    return penalties


def append_profits(clients):
    """
    Appends profits to the client dictionary.

    Parameters:
        clients (dict): {
            'client_1': {
                'probabilities': {idEmisora: probability, ...},
                'bank': 'BANK_NAME'
            },
            ...
        }

    Returns:
        dict: Same structure but with appended profits.
    """

    for client_id, data in clients.items():
        data["profits"] = compute_profits_for_client(data)

    return clients

def calculate_best_emisora(clients):
    """
    Calculates the best emisora for each client based on profits.

    Parameters:
        clients (dict): {
            'client_1': {
                'probabilities': {idEmisora: probability, ...},
                'bank': 'BANK_NAME'
            },
            ...
        }

    Returns:
        dict: Same structure but with appended best emisora.
    """

    for client_id, data in clients.items():
        profits = data["profits"]
        # best_emisora = max(profits, key=profits.get)
        # Filter out keys where the value is None
        # valid_profits = {k: v for k, v in profits.items() if v is not None}

        # # Then safely compute the minimum
        # best_emisora = min(valid_profits, key=valid_profits.get) if valid_profits else None

        best_emisora = max(profits, key=profits.get)
        data["best_emisora"] = best_emisora

    return clients