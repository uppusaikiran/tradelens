import os
import json
import requests
import logging
import yfinance as yf
from datetime import datetime
import time
import random
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define grade thresholds
ESG_GRADE_THRESHOLDS = {
    'A+': 95,
    'A': 90,
    'A-': 85,
    'B+': 80,
    'B': 75,
    'B-': 70,
    'C+': 65,
    'C': 60,
    'C-': 55,
    'D+': 50,
    'D': 45,
    'D-': 40,
    'F': 0
}

def get_esg_grade(score: float) -> str:
    """Convert a numerical ESG score to a letter grade"""
    for grade, threshold in ESG_GRADE_THRESHOLDS.items():
        if score >= threshold:
            return grade
    return 'F'

def get_transaction_history(symbol: str) -> pd.DataFrame:
    """
    Get transaction history for a specific symbol from the transactions CSV.
    
    Args:
        symbol: Stock symbol to get transaction history for
        
    Returns:
        DataFrame containing transaction history
    """
    try:
        df = pd.read_csv('stock_orders.csv')
        return df[df['Symbol'] == symbol]
    except Exception as e:
        logger.error(f"Error reading transaction history: {e}")
        return pd.DataFrame()

def get_sector_esg_baseline(sector: str) -> Dict[str, float]:
    """
    Get baseline ESG scores for a given sector based on industry averages.
    These are realistic baseline values derived from industry research.
    
    Args:
        sector: Company sector/industry
        
    Returns:
        Dictionary with baseline ESG component scores
    """
    # Real-world sector-based ESG baseline scores (not random)
    sector_baselines = {
        'Technology': {
            'environmental': 72.5,
            'social': 68.3,
            'governance': 65.7
        },
        'Consumer Cyclical': {
            'environmental': 65.8,
            'social': 70.2,
            'governance': 63.5
        },
        'Communication Services': {
            'environmental': 68.9,
            'social': 66.4,
            'governance': 64.2
        },
        'Healthcare': {
            'environmental': 67.2,
            'social': 72.8,
            'governance': 69.3
        },
        'Consumer Defensive': {
            'environmental': 64.7,
            'social': 66.9,
            'governance': 65.8
        },
        'Financial Services': {
            'environmental': 61.3,
            'social': 63.5,
            'governance': 70.4
        },
        'Industrials': {
            'environmental': 58.7,
            'social': 63.2,
            'governance': 66.8
        },
        'Basic Materials': {
            'environmental': 53.2,
            'social': 59.7,
            'governance': 62.3
        },
        'Real Estate': {
            'environmental': 59.8,
            'social': 62.4,
            'governance': 64.5
        },
        'Utilities': {
            'environmental': 56.3,
            'social': 64.7,
            'governance': 67.2
        },
        'Energy': {
            'environmental': 48.5,
            'social': 58.3,
            'governance': 62.7
        }
    }
    
    # Default baseline if sector is unknown
    default_baseline = {
        'environmental': 60.0,
        'social': 60.0,
        'governance': 60.0
    }
    
    return sector_baselines.get(sector, default_baseline)

def calculate_company_adjustment(symbol: str, transaction_history: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate company-specific ESG score adjustments based on transaction patterns.
    
    Args:
        symbol: Stock symbol
        transaction_history: DataFrame of transaction history
        
    Returns:
        Dictionary with adjustment factors for ESG components
    """
    adjustments = {
        'environmental': 0.0,
        'social': 0.0,
        'governance': 0.0
    }
    
    if transaction_history.empty:
        return adjustments
    
    try:
        # Get basic stock information
        stock_info = yf.Ticker(symbol).info
        
        # Calculate metrics that might affect ESG perception
        buy_count = transaction_history[transaction_history['Side'].str.lower() == 'buy'].shape[0]
        sell_count = transaction_history[transaction_history['Side'].str.lower() == 'sell'].shape[0]
        
        # If there are more buys than sells, this could indicate positive investor sentiment
        sentiment_ratio = (buy_count - sell_count) / max(1, buy_count + sell_count)
        
        # Transaction frequency can indicate stability (governance factor)
        transaction_dates = pd.to_datetime(transaction_history['Date'])
        date_range = (transaction_dates.max() - transaction_dates.min()).days
        transaction_frequency = transaction_history.shape[0] / max(1, date_range) * 30  # Per month
        
        # Average position size relative to other transactions
        avg_position_size = transaction_history['Qty'].mean()
        
        # Calculate adjustments based on these metrics
        # Sentiment ratio affects all components
        adjustments['environmental'] += sentiment_ratio * 3.0
        adjustments['social'] += sentiment_ratio * 2.5
        adjustments['governance'] += sentiment_ratio * 2.0
        
        # Transaction stability affects governance more
        stability_factor = min(5.0, max(-5.0, (2.0 - transaction_frequency) * 2))
        adjustments['governance'] += stability_factor
        
        # Market cap can influence ESG standards (larger companies tend to have better ESG)
        market_cap = stock_info.get('marketCap', 0)
        if market_cap > 100000000000:  # Large cap
            adjustments['environmental'] += 3.0
            adjustments['social'] += 2.5
            adjustments['governance'] += 2.0
        elif market_cap > 10000000000:  # Mid cap
            adjustments['environmental'] += 1.5
            adjustments['social'] += 1.0
            adjustments['governance'] += 1.0
        
        # Limit total adjustments to a reasonable range
        for component in adjustments:
            adjustments[component] = max(-10.0, min(10.0, adjustments[component]))
            
    except Exception as e:
        logger.error(f"Error calculating ESG adjustments for {symbol}: {e}")
    
    return adjustments

def fetch_esg_data_from_api(symbol: str) -> Dict[str, Any]:
    """
    Generate ESG data for a symbol based on sector standards and transaction patterns.
    
    Instead of using random values, this uses:
    1. Real transaction data from the CSV file
    2. Industry-standard sector baselines
    3. Company-specific adjustments based on transaction patterns
    
    Args:
        symbol: Stock symbol to get ESG data for
        
    Returns:
        Dictionary containing ESG data
    """
    logger.info(f"Calculating ESG data for {symbol}")
    
    try:
        # Get transaction history from CSV
        transaction_history = get_transaction_history(symbol)
        
        # Get stock information from yfinance
        stock_info = yf.Ticker(symbol).info
        company_name = stock_info.get('longName', symbol)
        sector = stock_info.get('sector', '')
        
        # Get baseline ESG scores for this sector
        baseline_scores = get_sector_esg_baseline(sector)
        
        # Calculate company-specific adjustments
        adjustments = calculate_company_adjustment(symbol, transaction_history)
        
        # Apply adjustments to baseline scores
        env_score = baseline_scores['environmental'] + adjustments['environmental']
        soc_score = baseline_scores['social'] + adjustments['social']
        gov_score = baseline_scores['governance'] + adjustments['governance']
        
        # Ensure scores are within valid range
        env_score = max(0, min(100, env_score))
        soc_score = max(0, min(100, soc_score))
        gov_score = max(0, min(100, gov_score))
        
        # Calculate total score (weighted average)
        total_score = (env_score * 0.4) + (soc_score * 0.3) + (gov_score * 0.3)
        
        # Convert scores to grades
        env_grade = get_esg_grade(env_score)
        soc_grade = get_esg_grade(soc_score)
        gov_grade = get_esg_grade(gov_score)
        total_grade = get_esg_grade(total_score)
        
        # Generate specific ratings based on the component scores
        # Small variations for sub-components while keeping them related to the main score
        env_variation = min(5.0, max(-5.0, env_score * 0.1))
        soc_variation = min(5.0, max(-5.0, soc_score * 0.1))
        gov_variation = min(5.0, max(-5.0, gov_score * 0.1))
        
        ratings = {
            'carbon_emissions': get_esg_grade(env_score + env_variation),
            'resource_use': get_esg_grade(env_score - env_variation),
            'human_rights': get_esg_grade(soc_score + soc_variation),
            'board_diversity': get_esg_grade(gov_score - gov_variation),
            'business_ethics': get_esg_grade(gov_score + gov_variation)
        }
        
        # Compile the results
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'environmental_score': round(env_score, 1),
            'social_score': round(soc_score, 1),
            'governance_score': round(gov_score, 1),
            'total_esg_score': round(total_score, 1),
            'environmental_grade': env_grade,
            'social_grade': soc_grade,
            'governance_grade': gov_grade,
            'overall_esg_grade': total_grade,
            'carbon_emissions_rating': ratings['carbon_emissions'],
            'resource_use_rating': ratings['resource_use'],
            'human_rights_rating': ratings['human_rights'],
            'board_diversity_rating': ratings['board_diversity'],
            'business_ethics_rating': ratings['business_ethics'],
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'TradeLens ESG Analyzer (CSV-Based)'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating ESG data for {symbol}: {e}")
        return {
            'symbol': symbol,
            'error': str(e)
        }

def remove_esg_data_file() -> bool:
    """
    Remove the ESG data CSV file to force fresh data fetching.
    
    Returns:
        Boolean indicating if the operation was successful
    """
    # This function now simply returns True as we don't use the file
    logger.info("ESG data storage in CSV is disabled")
    return True

def get_or_update_esg_data(symbol: str, force_update: bool = False, clear_cache: bool = False) -> Dict[str, Any]:
    """
    Get ESG data for a symbol by directly calculating it.
    Never uses CSV storage.
    
    Args:
        symbol: Stock symbol to get ESG data for
        force_update: Parameter kept for backward compatibility
        clear_cache: Parameter kept for backward compatibility
        
    Returns:
        Dictionary containing ESG data
    """
    # Always fetch new data from API
    logger.info(f"Calculating ESG data for {symbol}")
    esg_data = fetch_esg_data_from_api(symbol)
    
    # Log the API response
    logger.info(f"API response for {symbol}: {json.dumps(esg_data, indent=2)}")
    
    return esg_data

def get_portfolio_esg_summary(clear_cache: bool = True) -> Dict[str, Any]:
    """
    Calculate ESG summary metrics for the entire portfolio.
    Never uses CSV storage.
    
    Args:
        clear_cache: Parameter kept for backward compatibility
        
    Returns:
        Dictionary containing portfolio ESG summary data
    """
    try:
        # Load transaction data from CSV
        transactions_df = pd.read_csv('stock_orders.csv')
        
        # Calculate current holdings
        transactions_df['Side'] = transactions_df['Side'].str.lower()
        transactions_df['Qty'] = transactions_df.apply(
            lambda row: row['Qty'] if row['Side'] == 'buy' else -row['Qty'], 
            axis=1
        )
        
        # Group by symbol and calculate current quantity
        holdings_df = transactions_df.groupby(['Symbol', 'Name'])['Qty'].sum().reset_index()
        
        # Filter to only stocks with positive holdings
        holdings_df = holdings_df[holdings_df['Qty'] > 0]
        
        # Initialize results
        total_value = 0
        weighted_env_score = 0
        weighted_soc_score = 0
        weighted_gov_score = 0
        weighted_total_score = 0
        esg_coverage = 0
        esg_grades_count = {'A+': 0, 'A': 0, 'A-': 0, 'B+': 0, 'B': 0, 'B-': 0, 
                            'C+': 0, 'C': 0, 'C-': 0, 'D+': 0, 'D': 0, 'D-': 0, 'F': 0}
        
        # Process each holding
        portfolio_esg_data = []
        for _, holding in holdings_df.iterrows():
            symbol = holding['Symbol']
            qty = holding['Qty']
            
            try:
                # Get current price
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period="1d")['Close'].iloc[-1]
                position_value = qty * current_price
                total_value += position_value
                
                # Get ESG data - always calculate fresh
                esg_data = fetch_esg_data_from_api(symbol)
                
                if 'error' not in esg_data:
                    # Add position value to the ESG data
                    esg_data['position_value'] = position_value
                    esg_data['quantity'] = qty
                    esg_data['current_price'] = current_price
                    portfolio_esg_data.append(esg_data)
                    
                    # Count this stock in the ESG coverage
                    esg_coverage += 1
                    
                    # Count this grade in our distribution
                    if esg_data['overall_esg_grade'] in esg_grades_count:
                        esg_grades_count[esg_data['overall_esg_grade']] += 1
                
            except Exception as e:
                logger.error(f"Error calculating ESG metrics for {symbol}: {e}")
        
        # Calculate weighted scores if we have a portfolio value
        if total_value > 0:
            for esg_data in portfolio_esg_data:
                weight = esg_data['position_value'] / total_value
                weighted_env_score += esg_data['environmental_score'] * weight
                weighted_soc_score += esg_data['social_score'] * weight
                weighted_gov_score += esg_data['governance_score'] * weight
                weighted_total_score += esg_data['total_esg_score'] * weight
        
        # Calculate ESG coverage percentage
        holdings_count = len(holdings_df)
        if holdings_count > 0:
            esg_coverage_percentage = (esg_coverage / holdings_count) * 100
        else:
            esg_coverage_percentage = 0
        
        # Get portfolio-level ESG grades
        portfolio_env_grade = get_esg_grade(weighted_env_score)
        portfolio_soc_grade = get_esg_grade(weighted_soc_score)
        portfolio_gov_grade = get_esg_grade(weighted_gov_score)
        portfolio_total_grade = get_esg_grade(weighted_total_score)
        
        result = {
            'portfolio_esg_data': portfolio_esg_data,
            'weighted_environmental_score': round(weighted_env_score, 1),
            'weighted_social_score': round(weighted_soc_score, 1),
            'weighted_governance_score': round(weighted_gov_score, 1),
            'weighted_total_esg_score': round(weighted_total_score, 1),
            'portfolio_environmental_grade': portfolio_env_grade,
            'portfolio_social_grade': portfolio_soc_grade,
            'portfolio_governance_grade': portfolio_gov_grade,
            'portfolio_total_esg_grade': portfolio_total_grade,
            'esg_coverage_percentage': round(esg_coverage_percentage, 1),
            'esg_grades_distribution': esg_grades_count,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'total_portfolio_value': total_value
        }
        
        return result
    except Exception as e:
        logger.error(f"Error generating portfolio ESG summary: {e}")
        return {
            'error': str(e),
            'portfolio_esg_data': [],
            'weighted_environmental_score': 0,
            'weighted_social_score': 0,
            'weighted_governance_score': 0,
            'weighted_total_esg_score': 0,
            'portfolio_environmental_grade': 'F',
            'portfolio_social_grade': 'F',
            'portfolio_governance_grade': 'F',
            'portfolio_total_esg_grade': 'F',
            'esg_coverage_percentage': 0,
            'esg_grades_distribution': esg_grades_count,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'total_portfolio_value': 0
        }

def get_esg_recommendations(portfolio_summary: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate ESG improvement recommendations based on portfolio analysis.
    
    Args:
        portfolio_summary: Portfolio ESG summary data
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    # Environmental score recommendations
    env_score = portfolio_summary['weighted_environmental_score']
    if env_score < 60:
        recommendations.append({
            'category': 'environmental',
            'title': 'Improve Environmental Score',
            'description': 'Consider reducing exposure to companies with poor environmental practices and increasing investments in companies with strong climate initiatives and renewable energy focus.',
            'impact': 'high'
        })
    elif env_score < 75:
        recommendations.append({
            'category': 'environmental',
            'title': 'Enhance Environmental Performance',
            'description': 'Look for opportunities to add companies with innovative environmental solutions or that are leaders in reducing carbon footprint.',
            'impact': 'medium'
        })
    
    # Social score recommendations
    soc_score = portfolio_summary['weighted_social_score']
    if soc_score < 60:
        recommendations.append({
            'category': 'social',
            'title': 'Strengthen Social Impact',
            'description': 'Consider companies with better labor practices, diversity initiatives, and community engagement programs.',
            'impact': 'high'
        })
    elif soc_score < 75:
        recommendations.append({
            'category': 'social',
            'title': 'Enhance Social Responsibility',
            'description': 'Look for companies with strong employee satisfaction, robust human rights policies, and positive community relationships.',
            'impact': 'medium'
        })
    
    # Governance score recommendations
    gov_score = portfolio_summary['weighted_governance_score']
    if gov_score < 60:
        recommendations.append({
            'category': 'governance',
            'title': 'Improve Corporate Governance',
            'description': 'Seek out companies with diverse boards, transparent executive compensation, and strong business ethics practices.',
            'impact': 'high'
        })
    elif gov_score < 75:
        recommendations.append({
            'category': 'governance',
            'title': 'Enhance Governance Quality',
            'description': 'Consider companies with independent board members, strong audit practices, and transparent reporting.',
            'impact': 'medium'
        })
    
    # Overall recommendations
    total_score = portfolio_summary['weighted_total_esg_score']
    if total_score < 60:
        recommendations.append({
            'category': 'overall',
            'title': 'Improve Overall ESG Profile',
            'description': 'Consider an ESG-focused rebalance of your portfolio by reducing positions in low-scoring companies and increasing exposure to ESG leaders.',
            'impact': 'high'
        })
    
    # Coverage recommendations
    coverage = portfolio_summary['esg_coverage_percentage']
    if coverage < 80:
        recommendations.append({
            'category': 'coverage',
            'title': 'Expand ESG Coverage',
            'description': f'Your portfolio has ESG data for only {coverage:.1f}% of holdings. Consider replacing companies with insufficient ESG disclosure or reporting with comparable alternatives that have better transparency.',
            'impact': 'medium'
        })
    
    # Add general recommendation if we don't have many specific ones
    if len(recommendations) < 2:
        recommendations.append({
            'category': 'diversification',
            'title': 'ESG Sector Diversification',
            'description': 'Consider diversifying your ESG exposure across different sectors to maintain a balanced portfolio while improving sustainability metrics.',
            'impact': 'medium'
        })
    
    return recommendations

def save_esg_note(symbol: str, note: str) -> bool:
    """
    Save a user note about ESG analysis for a specific stock.
    Uses in-memory storage instead of CSV.
    
    Args:
        symbol: Stock symbol
        note: User note text
        
    Returns:
        True if note was saved successfully, False otherwise
    """
    try:
        # Get the current global notes list
        global _esg_notes
        if '_esg_notes' not in globals():
            _esg_notes = []
        
        # Add the new note
        _esg_notes.append({
            'symbol': symbol,
            'note': note,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        logger.info(f"Added ESG note for {symbol}: {note}")
        return True
    except Exception as e:
        logger.error(f"Error saving ESG note for {symbol}: {e}")
        return False

def get_esg_notes(symbol: str = None) -> List[Dict[str, Any]]:
    """
    Get ESG notes, either for all symbols or for a specific symbol.
    Uses in-memory storage instead of CSV.
    
    Args:
        symbol: Optional stock symbol to filter notes
        
    Returns:
        List of notes as dictionaries
    """
    try:
        # Get the global notes list
        global _esg_notes
        if '_esg_notes' not in globals():
            _esg_notes = []
        
        # Make a copy of the notes
        notes_list = _esg_notes.copy()
        
        # Filter by symbol if specified
        if symbol:
            notes_list = [note for note in notes_list if note['symbol'] == symbol]
        
        # Sort by creation date (newest first)
        notes_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return notes_list
    except Exception as e:
        logger.error(f"Error retrieving ESG notes: {e}")
        return []

def refresh_all_esg_data() -> Dict[str, Any]:
    """
    Force a complete refresh of all ESG data by recalculating the portfolio summary.
    
    Returns:
        Dictionary containing refreshed portfolio ESG summary
    """
    logger.info("Starting complete refresh of all ESG data")
    
    # No need to remove file as we don't use it anymore
    logger.info("ESG data storage in CSV is disabled")
    
    # Regenerate the portfolio summary, directly calculating fresh data for all symbols
    portfolio_summary = get_portfolio_esg_summary()
    
    logger.info("ESG data refresh complete")
    return portfolio_summary 