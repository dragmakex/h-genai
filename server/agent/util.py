from datetime import datetime
from typing import Tuple, Dict, Any, List, Union

import pandas as pd
import requests

def _process_financial_results(results: List[Dict[str, Any]], year: str, is_commune: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Helper function to process financial results and create DataFrames and metrics.
    
    Args:
        results: List of financial data results from API containing dictionaries with financial metrics
        year: Year of the data as a string in YYYY format
        is_commune: Whether processing commune (True) or EPCI (False) data
        
    Returns:
        Tuple containing:
            - pd.DataFrame: Profile information with basic details about the entity
            - pd.DataFrame: Financial details with metrics and amounts
            - Dict[str, Any]: Key financial metrics including:
                - population (int): Total population
                - data_from_year (int): Year of the data
                - total_budget (float): Total budget amount
                - total_budget_per_person (float): Budget per capita
                - debt_repayment_capacity (float | None): Debt repayment capacity ratio
                - debt_ratio (float | None): Debt to revenue ratio as percentage
                - debt_duration (float | None): Years to repay debt at current rate
                - management_savings_per_capita (float): Management savings per capita
                - management_savings_ratio (float): Management savings ratio
                - gross_savings_per_capita (float): Gross savings per capita
                - gross_savings_ratio (float): Gross savings ratio
                - net_savings_per_capita (float): Net savings per capita
                - net_savings_ratio (float): Net savings ratio
                - debt_service_to_operating_revenue_ratio (float): Debt service to operating revenue ratio
    """
    if not results:
        return pd.DataFrame(), pd.DataFrame(), {}

    # Create profile DataFrame
    basic_info = results[0]
    if is_commune:
        profile_data = [
            ["Name", basic_info['com_name']],
            ["SIREN", basic_info['siren']],
            ["INSEE Code", basic_info['insee']],
            ["Population", f"{basic_info['ptot']:,}"],
            ["Intercommunality", basic_info['epci_name']]
        ]
        financial_cols = [
            'agregat', 'montant', 'euros_par_habitant',
            'montant_bp', 'montant_ba', 'montant_flux'
        ]
        col_names = [
            'Metric', 'Total Amount (€)', 'Per Capita (€)',
            'Primary Budget (€)', 'Annexed Budget (€)', 'Flow Amount (€)'
        ]
    else:
        profile_data = [
            ["Name", basic_info['epci_name']],
            ["EPCI Code", basic_info['epci_code']],
            ["SIREN", basic_info['siren']],
            ["Legal Status", basic_info['nat_juridique']],
            ["Population", f"{basic_info['ptot']:,}"],
            ["Department", basic_info['dep_name'][0]],
            ["Region", basic_info['reg_name'][0]]
        ]
        financial_cols = [
            'agregat', 'montant', 'euros_par_habitant',
            'montant_gfp', 'montant_communes', 'montant_flux'
        ]
        col_names = [
            'Metric', 'Total Amount (€)', 'Per Capita (€)',
            'EPCI Amount (€)', 'Communes Amount (€)', 'Flow Amount (€)'
        ]

    profile_df = pd.DataFrame(profile_data, columns=['Field', 'Value'])

    # Create financial details DataFrame
    financial_df = pd.DataFrame(results)
    financial_df = financial_df[financial_cols]
    financial_df.columns = col_names

    # Format numeric columns
    numeric_columns = financial_df.columns[1:]
    for col in numeric_columns:
        financial_df[col] = financial_df[col].apply(lambda x: f"{x:,.2f}")

    # Extract key metrics
    total_budget = float(financial_df.loc[financial_df['Metric'] == 'Encours de dette', 'Total Amount (€)'].iloc[0].replace(',', ''))
    total_budget_per_person = float(financial_df.loc[financial_df['Metric'] == 'Encours de dette', 'Per Capita (€)'].iloc[0].replace(',', ''))
    
    gross_savings = float(financial_df.loc[financial_df['Metric'] == 'Epargne brute', 'Total Amount (€)'].iloc[0].replace(',', ''))
    operating_revenue = float(financial_df.loc[financial_df['Metric'] == 'Recettes de fonctionnement', 'Total Amount (€)'].iloc[0].replace(',', ''))
    remb_emprunts = float(financial_df.loc[financial_df['Metric'] == "Remboursements d'emprunts hors GAD", 'Total Amount (€)'].iloc[0].replace(',', ''))

    # Get debt service ratio HC
    debt_service = float(financial_df.loc[financial_df['Metric'] == 'Annuité de la dette', 'Total Amount (€)'].iloc[0].replace(',', ''))
    debt_service_to_operating_revenue_ratio = (debt_service / operating_revenue) * 100

    # Get savings metrics (EG, EB, EN)
    management_savings_per_capita = float(financial_df.loc[financial_df['Metric'] == 'Epargne de gestion', 'Per Capita (€)'].iloc[0].replace(',', ''))
    gross_savings_per_capita = float(financial_df.loc[financial_df['Metric'] == 'Epargne brute', 'Per Capita (€)'].iloc[0].replace(',', ''))
    net_savings_per_capita = float(financial_df.loc[financial_df['Metric'] == 'Epargne nette', 'Per Capita (€)'].iloc[0].replace(',', ''))

    # Get savings ratios
    management_savings = float(financial_df.loc[financial_df['Metric'] == 'Epargne de gestion', 'Total Amount (€)'].iloc[0].replace(',', ''))
    gross_expenses = float(financial_df.loc[financial_df['Metric'] == 'Recettes totales', 'Total Amount (€)'].iloc[0].replace(',', ''))
    management_savings_ratio = (management_savings / gross_expenses) * 100 # EG/RG
    
    gross_savings_ratio = (gross_savings / operating_revenue) * 100 # EB/RF
    net_savings = float(financial_df.loc[financial_df['Metric'] == 'Epargne nette', 'Total Amount (€)'].iloc[0].replace(',', ''))
    net_savings_ratio = (net_savings / operating_revenue) * 100 # EN/RF

    metrics = {
        'population': basic_info['ptot'],
        'data_from_year': int(year),
        'total_budget': round(total_budget),
        'total_budget_per_person': round(total_budget_per_person),
        'debt_repayment_capacity': round(total_budget / gross_savings, 1) if gross_savings != 0 else None,
        'debt_ratio': round((total_budget / operating_revenue * 100), 2) if operating_revenue != 0 else None,
        'debt_duration': round((total_budget / remb_emprunts), 1) if remb_emprunts != 0 else None,
        'management_savings_per_capita': round(management_savings_per_capita),
        'management_savings_ratio': round(management_savings_ratio, 2),
        'gross_savings_per_capita': round(gross_savings_per_capita),
        'gross_savings_ratio': round(gross_savings_ratio, 2),
        'net_savings_per_capita': round(net_savings_per_capita),
        'net_savings_ratio': round(net_savings_ratio, 2),
        'debt_service_to_operating_revenue_ratio': round(debt_service_to_operating_revenue_ratio, 2)
    }

    return profile_df, financial_df, metrics

def get_commune_finances_by_siren(
    siren: str,
    year: str = "2023"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Union[int, float, None]]]:
    """Get detailed financial data for a commune using its SIREN number.
    
    Makes an API request to retrieve financial data for a specific commune and processes
    the results into structured DataFrames and metrics.
    
    Args:
        siren: SIREN number of the commune as a 9-digit string
        year: Year of data as a string in YYYY format, valid range 2016-2023. Defaults to "2023"
        
    Returns:
        Tuple containing:
            - pd.DataFrame: Profile information with basic details about the commune
            - pd.DataFrame: Financial details with metrics and amounts
            - Dict[str, Union[int, float, None]]: Key financial metrics including:
                - population (int): Total population
                - data_from_year (int): Year of the data
                - total_budget (float): Total budget amount
                - total_budget_per_person (float): Budget per capita
                - debt_repayment_capacity (float | None): Debt repayment capacity ratio
                - debt_ratio (float | None): Debt to revenue ratio as percentage
                - debt_duration (float | None): Years to repay debt at current rate
                - management_savings_per_capita (float): Management savings per capita
                - management_savings_ratio (float): Management savings ratio
                - gross_savings_per_capita (float): Gross savings per capita
                - gross_savings_ratio (float): Gross savings ratio
                - net_savings_per_capita (float): Net savings per capita
                - net_savings_ratio (float): Net savings ratio
                - debt_service_to_operating_revenue_ratio (float): Debt service to operating revenue ratio
    """
    base_url = "https://data.ofgl.fr/api/explore/v2.1/catalog/datasets"
    dataset = "ofgl-base-communes-consolidee"
    endpoint = f"{base_url}/{dataset}/export/json"

    # Ensure year is a properly formatted 4-digit string
    year = str(datetime.strptime(year, "%Y").year)  # Converts to YYYY format

    params = {
        "where": f"siren='{siren}' AND year(exer)='{year}'",
        "order_by": "agregat",
        "select": ("exer,com_name,siren,insee,agregat,montant,montant_bp,montant_ba,"
                  "montant_flux,euros_par_habitant,ptot,rural,montagne,"
                  "touristique,qpv,epci_name")
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        results = response.json()
        return _process_financial_results(results, year, is_commune=True)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return pd.DataFrame(), pd.DataFrame(), {}

def get_epci_finances_by_code(
    epci_code: str,
    year: str = "2023"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Union[int, float, None]]]:
    """Get detailed financial data for an EPCI using its code.
    
    Makes an API request to retrieve financial data for a specific EPCI (Public Establishment 
    for Intercommunal Cooperation) and processes the results into structured DataFrames and metrics.
    
    Args:
        epci_code: EPCI identification code as a string
        year: Year of data as a string in YYYY format, valid range 2016-2023. Defaults to "2023"
        
    Returns:
        Tuple containing:
            - pd.DataFrame: Profile information with basic details about the EPCI
            - pd.DataFrame: Financial details with metrics and amounts
            - Dict[str, Union[int, float, None]]: Key financial metrics including:
                - population (int): Total population
                - data_from_year (int): Year of the data
                - total_budget (float): Total budget amount
                - total_budget_per_person (float): Budget per capita
                - debt_repayment_capacity (float | None): Debt repayment capacity ratio
                - debt_ratio (float | None): Debt to revenue ratio as percentage
                - debt_duration (float | None): Years to repay debt at current rate
                - management_savings_per_capita (float): Management savings per capita
                - management_savings_ratio (float): Management savings ratio
                - gross_savings_per_capita (float): Gross savings per capita
                - gross_savings_ratio (float): Gross savings ratio
                - net_savings_per_capita (float): Net savings per capita
                - net_savings_ratio (float): Net savings ratio
                - debt_service_to_operating_revenue_ratio (float): Debt service to operating revenue ratio
    """
    base_url = "https://data.ofgl.fr/api/explore/v2.1/catalog/datasets"
    dataset = "ofgl-base-ei"
    endpoint = f"{base_url}/{dataset}/export/json"

    # Ensure year is a properly formatted 4-digit string
    year = str(datetime.strptime(year, "%Y").year)  # Converts to YYYY format

    params = {
        "where": f"epci_code='{epci_code}' AND year(exer)='{year}'",
        "order_by": "agregat",
        "select": ("exer,epci_name,epci_code,siren,agregat,montant,montant_gfp,montant_communes,"
                  "montant_flux,euros_par_habitant,ptot,nat_juridique,mode_financement,"
                  "gfp_qpv,reg_name,dep_name")
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        results = response.json()
        return _process_financial_results(results, year, is_commune=False)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return pd.DataFrame(), pd.DataFrame(), {}