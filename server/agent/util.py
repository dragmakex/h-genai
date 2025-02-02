from datetime import datetime
from typing import Tuple, Dict, Any

import pandas as pd
import requests

def get_commune_finances_by_siren(
    siren: str,
    year: str = "2023"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Get detailed financial data for a commune using its SIREN number.
    
    Args:
        siren: SIREN number of the commune (9 digits)
        year: Year of data (2016-2023), should be a 4-digit string
        
    Returns:
        Tuple containing:
            - pd.DataFrame: Profile information with basic details about the commune
            - pd.DataFrame: Financial details with metrics and amounts
            - Dict[str, Any]: Key financial metrics including:
                - total_budget (float): Total budget amount
                - total_budget_per_person (float): Budget per capita
                - population (int): Total population
                - data_from_year (int): Year of the data
                - debt_repayment_capacity (float | None): Debt repayment capacity ratio
                - debt_ratio (float | None): Debt to revenue ratio as percentage
                - debt_duration (float | None): Years to repay debt at current rate
    """
    base_url = "https://data.ofgl.fr/api/explore/v2.1/catalog/datasets"
    dataset = "ofgl-base-communes-consolidee"
    endpoint = f"{base_url}/{dataset}/records"

    # Ensure year is a properly formatted 4-digit string
    year = str(datetime.strptime(year, "%Y").year)  # Converts to YYYY format

    params = {
        "limit": 100,
        "where": f"siren='{siren}' AND year(exer)='{year}'",
        "order_by": "agregat",
        "select": ("exer,com_name,siren,insee,agregat,montant,montant_bp,montant_ba,"
                  "montant_flux,euros_par_habitant,ptot,rural,montagne,"
                  "touristique,qpv,epci_name")
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])

        if not results:
            print(f"No data found for SIREN {siren} in year {year}")
            return pd.DataFrame(), pd.DataFrame(), {}

        # Create profile DataFrame
        basic_info = results[0]
        profile_df = pd.DataFrame([
            ["Name", basic_info['com_name']],
            ["SIREN", basic_info['siren']],
            ["INSEE Code", basic_info['insee']],
            ["Population", f"{basic_info['ptot']:,}"],
            ["Intercommunality", basic_info['epci_name']]
        ], columns=['Field', 'Value'])

        # Create financial details DataFrame
        financial_df = pd.DataFrame(results)
        financial_df = financial_df[[
            'agregat', 'montant', 'euros_par_habitant', 
            'montant_bp', 'montant_ba', 'montant_flux'
        ]]
        financial_df.columns = [
            'Metric', 'Total Amount (€)', 'Per Capita (€)',
            'Primary Budget (€)', 'Annexed Budget (€)', 'Flow Amount (€)'
        ]
        
        # Format numeric columns
        numeric_columns = financial_df.columns[1:]
        for col in numeric_columns:
            financial_df[col] = financial_df[col].apply(lambda x: f"{x:,.2f}")

        # Extract key metrics
        metrics = {}
        for row in results:
            if row['agregat'] == 'Encours de dette':
                metrics['total_budget'] = row['montant']
                metrics['total_budget_per_person'] = row['euros_par_habitant']
            elif row['agregat'] == 'Epargne brute':
                epargne_brute = row['montant']
            elif row['agregat'] == 'Recettes de fonctionnement':
                recettes_fonct = row['montant']
            elif row['agregat'] == "Remboursements d'emprunts hors GAD":
                remb_emprunts = row['montant']

        metrics.update({
            'population': basic_info['ptot'],
            'data_from_year': int(year),
            'debt_repayment_capacity': metrics['total_budget'] / epargne_brute if epargne_brute != 0 else None,
            'debt_ratio': (metrics['total_budget'] / recettes_fonct * 100) if recettes_fonct != 0 else None,
            'debt_duration': (metrics['total_budget'] / remb_emprunts) if remb_emprunts != 0 else None
        })

        return profile_df, financial_df, metrics
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return pd.DataFrame(), pd.DataFrame(), {}
    

def get_epci_finances_by_code(
    epci_code: str,
    year: str = "2023"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Get detailed financial data for an EPCI (Public Establishment for Intercommunal Cooperation) using its code.
    
    Args:
        epci_code: EPCI identification code
        year: Year of data (2016-2023), should be a 4-digit string
        
    Returns:
        Tuple containing:
            - pd.DataFrame: Profile information with basic details about the EPCI
            - pd.DataFrame: Financial details with metrics and amounts
            - Dict[str, Any]: Key financial metrics including:
                - total_budget (float): Total budget amount
                - total_budget_per_person (float): Budget per capita
                - population (int): Total population
                - data_from_year (int): Year of the data
                - debt_repayment_capacity (float | None): Debt repayment capacity ratio
                - debt_ratio (float | None): Debt to revenue ratio as percentage
                - debt_duration (float | None): Years to repay debt at current rate
    """
    base_url = "https://data.ofgl.fr/api/explore/v2.1/catalog/datasets"
    dataset = "ofgl-base-ei"
    endpoint = f"{base_url}/{dataset}/records"

    # Ensure year is a properly formatted 4-digit string
    year = str(datetime.strptime(year, "%Y").year)  # Converts to YYYY format

    params = {
        "limit": 100,
        "where": f"epci_code='{epci_code}' AND year(exer)='{year}'",
        "order_by": "agregat",
        "select": ("exer,epci_name,epci_code,siren,agregat,montant,montant_gfp,montant_communes,"
                  "montant_flux,euros_par_habitant,ptot,nat_juridique,mode_financement,"
                  "gfp_qpv,reg_name,dep_name")
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])

        if not results:
            print(f"No data found for EPCI {epci_code} in year {year}")
            return pd.DataFrame(), pd.DataFrame(), {}

        # Create profile DataFrame
        basic_info = results[0]
        profile_df = pd.DataFrame([
            ["Name", basic_info['epci_name']],
            ["EPCI Code", basic_info['epci_code']],
            ["SIREN", basic_info['siren']],
            ["Legal Status", basic_info['nat_juridique']],
            ["Population", f"{basic_info['ptot']:,}"],
            ["Department", basic_info['dep_name'][0]],
            ["Region", basic_info['reg_name'][0]]
        ], columns=['Field', 'Value'])

        # Create financial details DataFrame
        financial_df = pd.DataFrame(results)
        financial_df = financial_df[[
            'agregat', 'montant', 'euros_par_habitant', 
            'montant_gfp', 'montant_communes', 'montant_flux'
        ]]
        financial_df.columns = [
            'Metric', 'Total Amount (€)', 'Per Capita (€)',
            'EPCI Amount (€)', 'Communes Amount (€)', 'Flow Amount (€)'
        ]
        
        # Format numeric columns
        numeric_columns = financial_df.columns[1:]
        for col in numeric_columns:
            financial_df[col] = financial_df[col].apply(lambda x: f"{x:,.2f}")

        # Extract key metrics
        metrics = {}
        for row in results:
            if row['agregat'] == 'Encours de dette':
                metrics['total_budget'] = row['montant']
                metrics['total_budget_per_person'] = row['euros_par_habitant']
            elif row['agregat'] == 'Epargne brute':
                epargne_brute = row['montant']
            elif row['agregat'] == 'Recettes de fonctionnement':
                recettes_fonct = row['montant']
            elif row['agregat'] == "Remboursements d'emprunts hors GAD":
                remb_emprunts = row['montant']

        metrics.update({
            'population': basic_info['ptot'],
            'data_from_year': int(year),
            'debt_repayment_capacity': metrics['total_budget'] / epargne_brute if epargne_brute != 0 else None,
            'debt_ratio': (metrics['total_budget'] / recettes_fonct * 100) if recettes_fonct != 0 else None,
            'debt_duration': (metrics['total_budget'] / remb_emprunts) if remb_emprunts != 0 else None
        })

        return profile_df, financial_df, metrics
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return pd.DataFrame(), pd.DataFrame(), {}