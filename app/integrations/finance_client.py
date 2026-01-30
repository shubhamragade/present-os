"""
Finance Client - Notion-Backed Budget Tracking for PresentOS

Reads expense data from Notion and calculates budget status.
Replaces mock implementation with real Notion queries.

Note: Investment portfolio remains simulated as brokerage APIs
require complex OAuth flows (Wealthfront, etc.).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger("presentos.finance_client")


class FinanceClient:
    """
    Finance client that uses Notion as the source of truth for expenses.
    
    Budget limits are configurable. Expenses are read from Notion.
    """
    
    # Default monthly budget limits per category
    DEFAULT_BUDGET_LIMITS = {
        "Dining": 500,
        "Groceries": 400,
        "Entertainment": 200,
        "Utilities": 150,
        "Transport": 300,
        "Shopping": 400,
        "Subscriptions": 100,
        "Health": 200,
        "General": 500,
    }
    
    def __init__(self, budget_limits: Optional[Dict[str, float]] = None):
        """
        Initialize FinanceClient.
        
        Args:
            budget_limits: Optional custom budget limits per category.
                          If not provided, uses DEFAULT_BUDGET_LIMITS.
        """
        self.budget_limits = budget_limits or self.DEFAULT_BUDGET_LIMITS.copy()
        self._notion = None
    
    @property
    def notion(self):
        """Lazy-load NotionClient to avoid circular imports."""
        if self._notion is None:
            from app.integrations.notion_client import NotionClient
            self._notion = NotionClient.from_env()
        return self._notion
    
    def _get_current_month_range(self) -> tuple[str, str]:
        """Get start and end dates for current month."""
        now = datetime.utcnow()
        start = now.replace(day=1).strftime("%Y-%m-%d")
        
        # Get last day of current month
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        
        end = end_date.strftime("%Y-%m-%d")
        return start, end
    
    def get_expenses_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, float]:
        """
        Get spending totals by category for a period.
        
        Args:
            start_date: ISO date string. Defaults to start of current month.
            end_date: ISO date string. Defaults to today.
        
        Returns:
            Dict mapping category names to total spent amounts.
        """
        if not start_date or not end_date:
            start_date, end_date = self._get_current_month_range()
        
        try:
            expenses = self.notion.get_expenses_by_period(start_date, end_date)
            
            # Aggregate by category
            by_category: Dict[str, float] = defaultdict(float)
            for expense in expenses:
                category = expense.get("category", "General")
                amount = expense.get("amount", 0)
                by_category[category] += amount
            
            return dict(by_category)
            
        except Exception as e:
            logger.error(f"Failed to get expenses summary: {e}")
            return {}
    
    def check_budget_status(self) -> Dict[str, Any]:
        """
        Check current month's budget status across all categories.
        
        Returns:
            Dict with:
                - status: "ok" | "warning" | "critical"
                - overruns: List of categories over budget
                - total_spent: Total spending this month
                - total_limit: Total budget limit
                - remaining: Amount remaining
                - by_category: Detailed breakdown per category
        """
        start_date, end_date = self._get_current_month_range()
        
        try:
            expenses = self.notion.get_expenses_by_period(start_date, end_date)
            
            # Aggregate by category
            spent_by_category: Dict[str, float] = defaultdict(float)
            for expense in expenses:
                category = expense.get("category", "General")
                amount = expense.get("amount", 0)
                spent_by_category[category] += amount
            
            # Calculate overruns and totals
            overruns = []
            warnings = []
            total_spent = 0
            total_limit = sum(self.budget_limits.values())
            by_category = {}
            
            for category, limit in self.budget_limits.items():
                spent = spent_by_category.get(category, 0)
                total_spent += spent
                
                percent = (spent / limit * 100) if limit > 0 else 0
                
                by_category[category] = {
                    "spent": spent,
                    "limit": limit,
                    "remaining": limit - spent,
                    "percent": round(percent, 1)
                }
                
                if spent > limit:
                    overruns.append({
                        "category": category,
                        "amount": round(spent - limit, 2),
                        "percent": round(percent, 1)
                    })
                elif percent >= 80:
                    warnings.append({
                        "category": category,
                        "percent": round(percent, 1)
                    })
            
            # Add any categories with spending that aren't in budget_limits
            for category, spent in spent_by_category.items():
                if category not in self.budget_limits:
                    by_category[category] = {
                        "spent": spent,
                        "limit": 0,
                        "remaining": -spent,
                        "percent": 100
                    }
                    total_spent += spent
            
            # Determine overall status
            if overruns:
                status = "critical" if len(overruns) > 2 else "warning"
            elif warnings:
                status = "warning"
            else:
                status = "ok"
            
            return {
                "status": status,
                "overruns": overruns,
                "warnings": warnings,
                "total_spent": round(total_spent, 2),
                "total_limit": total_limit,
                "remaining": round(total_limit - total_spent, 2),
                "by_category": by_category,
                "period": {
                    "start": start_date,
                    "end": end_date
                }
            }
            
        except Exception as e:
            logger.exception(f"Failed to check budget status: {e}")
            # Return safe fallback
            return {
                "status": "error",
                "error": str(e),
                "overruns": [],
                "total_spent": 0,
                "total_limit": sum(self.budget_limits.values()),
                "remaining": sum(self.budget_limits.values())
            }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get investment portfolio summary.
        
        Note: This remains simulated as investment APIs (Wealthfront, etc.)
        require complex OAuth flows. In production, integrate with your
        brokerage's API.
        
        Returns:
            Portfolio summary with total value and daily change.
        """
        # TODO: Replace with real brokerage API integration
        # For now, return reasonable mock data
        return {
            "total_value": 145000,
            "day_change": 1.2,  # percent
            "day_change_amount": 1740,
            "top_performer": "NVDA",
            "worst_performer": "BND",
            "source": "simulated"
        }
    
    def get_spending_trend(self, months: int = 3) -> List[Dict[str, Any]]:
        """
        Get spending trend over the last N months.
        
        Args:
            months: Number of months to analyze (default: 3)
        
        Returns:
            List of monthly spending summaries.
        """
        trends = []
        now = datetime.utcnow()
        
        for i in range(months):
            # Calculate month start/end
            if now.month - i <= 0:
                year = now.year - 1
                month = 12 + (now.month - i)
            else:
                year = now.year
                month = now.month - i
            
            start = datetime(year, month, 1).strftime("%Y-%m-%d")
            
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            end = end_date.strftime("%Y-%m-%d")
            
            try:
                expenses = self.notion.get_expenses_by_period(start, end)
                total = sum(e.get("amount", 0) for e in expenses)
                
                trends.append({
                    "month": f"{year}-{month:02d}",
                    "total_spent": round(total, 2),
                    "transaction_count": len(expenses)
                })
            except Exception as e:
                logger.warning(f"Failed to get trend for {year}-{month}: {e}")
                trends.append({
                    "month": f"{year}-{month:02d}",
                    "total_spent": 0,
                    "transaction_count": 0,
                    "error": True
                })
        
        return trends
