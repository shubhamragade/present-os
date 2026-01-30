"""
Notification Service - Proactive System Notifications
Handles evening summaries, XP alerts, weather notifications, task reminders
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("presentos.notifications")

@dataclass
class Notification:
    id: str
    type: str  # "xp_balance" | "evening_summary" | "weather_alert" | "task_reminder" | "meeting_summary"
    title: str
    message: str
    timestamp: str
    read: bool = False
    priority: str = "medium"  # "low" | "medium" | "high"
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: str = "default"

class NotificationService:
    """In-memory notification service (can be extended to use Notion/DB)"""
    
    def __init__(self):
        self._notifications: List[Notification] = []
        self._max_notifications = 100
        
    def create_notification(
        self,
        type: str,
        title: str,
        message: str,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = "default"
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            title=title,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            priority=priority,
            metadata=metadata or {},
            user_id=user_id
        )
        
        self._notifications.insert(0, notification)  # Add to front
        
        # Keep only recent notifications
        if len(self._notifications) > self._max_notifications:
            self._notifications = self._notifications[:self._max_notifications]
            
        logger.info(f"Created notification: {type} - {title}")
        return notification
    
    def get_notifications(
        self,
        user_id: str = "default",
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        filtered = [
            n for n in self._notifications
            if n.user_id == user_id and (not unread_only or not n.read)
        ]
        
        return [self._to_dict(n) for n in filtered[:limit]]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        for notif in self._notifications:
            if notif.id == notification_id:
                notif.read = True
                logger.info(f"Marked notification {notification_id} as read")
                return True
        return False
    
    def mark_all_as_read(self, user_id: str = "default") -> int:
        """Mark all notifications as read for a user"""
        count = 0
        for notif in self._notifications:
            if notif.user_id == user_id and not notif.read:
                notif.read = True
                count += 1
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count
    
    def get_unread_count(self, user_id: str = "default") -> int:
        """Get count of unread notifications"""
        return sum(1 for n in self._notifications if n.user_id == user_id and not n.read)
    
    def _to_dict(self, notification: Notification) -> Dict[str, Any]:
        """Convert notification to dict"""
        return {
            "id": notification.id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "timestamp": notification.timestamp,
            "read": notification.read,
            "priority": notification.priority,
            "metadata": notification.metadata
        }
    
    # ===== PROACTIVE NOTIFICATION GENERATORS =====
    
    def create_evening_summary(
        self,
        xp_data: Dict[str, int],
        task_count: int,
        suggestions: List[str],
        user_id: str = "default"
    ) -> Notification:
        """Create evening summary notification (PDF requirement)"""
        total_xp = xp_data.get("total", 0)
        
        # Find lagging PAEI
        paei_values = {k: v for k, v in xp_data.items() if k in ["P", "A", "E", "I"]}
        if paei_values:
            min_paei = min(paei_values, key=paei_values.get)
            min_value = paei_values[min_paei]
            min_percent = (min_value / total_xp * 100) if total_xp > 0 else 0
        else:
            min_paei = None
            min_percent = 0
        
        message = f"{task_count} tasks this week. Total XP: {total_xp}."
        
        if min_paei and min_percent < 20:
            paei_names = {"P": "Producer", "A": "Administrator", "E": "Entrepreneur", "I": "Integrator"}
            message += f" {paei_names[min_paei]} lagging at {min_percent:.0f}%."
        
        if suggestions:
            message += f" Suggestion: {suggestions[0]}"
        
        return self.create_notification(
            type="evening_summary",
            title="Quick check-in",
            message=message,
            priority="medium",
            metadata={"xp_data": xp_data, "task_count": task_count},
            user_id=user_id
        )
    
    def create_xp_balance_alert(
        self,
        lagging_role: str,
        percentage: float,
        suggestion: str,
        user_id: str = "default"
    ) -> Notification:
        """Create XP balance alert (PDF requirement)"""
        role_names = {"P": "Producer", "A": "Administrator", "E": "Entrepreneur", "I": "Integrator"}
        role_name = role_names.get(lagging_role, lagging_role)
        
        return self.create_notification(
            type="xp_balance",
            title="⚖️ PAEI Balance Alert",
            message=f"{role_name} lagging at {percentage:.0f}%. {suggestion}",
            priority="high",
            metadata={"role": lagging_role, "percentage": percentage},
            user_id=user_id
        )
    
    def create_weather_alert(
        self,
        condition: str,
        location: str,
        action_taken: str,
        user_id: str = "default"
    ) -> Notification:
        """Create weather alert (PDF requirement)"""
        return self.create_notification(
            type="weather_alert",
            title=f"🌊 {condition}",
            message=action_taken,
            priority="high",
            metadata={"condition": condition, "location": location},
            user_id=user_id
        )
    
    def create_task_reminder(
        self,
        task_title: str,
        due_date: str,
        task_id: Optional[str] = None,
        user_id: str = "default"
    ) -> Notification:
        """Create task reminder (PDF requirement)"""
        return self.create_notification(
            type="task_reminder",
            title="✅ Task Due Soon",
            message=f"'{task_title}' is due {due_date}",
            priority="medium",
            metadata={"task_id": task_id, "due_date": due_date},
            user_id=user_id
        )
    
    def create_meeting_summary(
        self,
        meeting_title: str,
        summary: str,
        meeting_id: Optional[str] = None,
        user_id: str = "default"
    ) -> Notification:
        """Create meeting summary notification (PDF requirement)"""
        return self.create_notification(
            type="meeting_summary",
            title=f"📧 Meeting Summary: {meeting_title}",
            message=summary,
            priority="low",
            metadata={"meeting_id": meeting_id},
            user_id=user_id
        )


# Global instance
_notification_service: Optional[NotificationService] = None

def get_notification_service() -> NotificationService:
    """Get or create the global notification service"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
