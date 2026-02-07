"""
Job Scheduler - Executes scheduled tasks (reminders, follow-ups, etc.)
======================================================================

Uses APScheduler for in-process scheduling.
Polls Supabase for scheduled jobs and executes them.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

# APScheduler for scheduling
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("[SCHEDULER] APScheduler not installed. Run: pip install apscheduler")

# Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from .orchestrator import get_orchestrator, SubstepStatus
from .executor import get_executor

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


class JobScheduler:
    """
    Handles scheduled job execution.
    
    - Polls database for pending jobs
    - Executes jobs at scheduled time
    - Updates task progress
    - Sends reminders
    """
    
    def __init__(self):
        self.scheduler = None
        self.client: Optional[Client] = None
        self.is_running = False
        
        # Initialize Supabase
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[SCHEDULER] Connected to Supabase")
            except Exception as e:
                print(f"[SCHEDULER] Supabase error: {e}")
        
        # Initialize APScheduler
        if SCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler()
            print("[SCHEDULER] APScheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            print("[SCHEDULER] Scheduler not available")
            return
        
        if self.is_running:
            return
        
        # Add job to poll for scheduled tasks every 30 seconds
        self.scheduler.add_job(
            self._poll_scheduled_jobs,
            IntervalTrigger(seconds=30),
            id="poll_scheduled_jobs",
            replace_existing=True
        )
        
        # Add job to check meeting status every minute
        self.scheduler.add_job(
            self._check_meeting_status,
            IntervalTrigger(minutes=1),
            id="check_meeting_status",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        print("[SCHEDULER] Started - polling every 30 seconds")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("[SCHEDULER] Stopped")
    
    async def _poll_scheduled_jobs(self):
        """Poll database for jobs that need to be executed"""
        
        if not self.client:
            return
        
        try:
            now = datetime.utcnow().isoformat()
            
            # Get pending jobs that are due
            result = self.client.table("scheduled_jobs").select("*").eq(
                "status", "pending"
            ).lte(
                "scheduled_for", now
            ).limit(10).execute()
            
            for job in result.data or []:
                asyncio.create_task(self._execute_job(job))
                
        except Exception as e:
            print(f"[SCHEDULER] Error polling jobs: {e}")
    
    async def _execute_job(self, job: Dict):
        """Execute a scheduled job"""
        
        job_id = job["id"]
        job_type = job["job_type"]
        job_params = job.get("job_params", {})
        
        print(f"[SCHEDULER] Executing job: {job_type} ({job_id})")
        
        try:
            # Mark as processing
            self.client.table("scheduled_jobs").update({
                "status": "processing",
                "started_at": datetime.utcnow().isoformat(),
                "attempts": job.get("attempts", 0) + 1
            }).eq("id", job_id).execute()
            
            result = None
            
            if job_type == "execute_substep":
                result = await self._execute_substep_job(job_params)
            elif job_type == "send_reminder":
                result = await self._send_reminder_job(job_params)
            elif job_type == "check_participant":
                result = await self._check_participant_job(job_params)
            else:
                result = {"message": f"Unknown job type: {job_type}"}
            
            # Mark as completed
            self.client.table("scheduled_jobs").update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "result": result
            }).eq("id", job_id).execute()
            
            print(f"[SCHEDULER] Job completed: {job_id}")
            
        except Exception as e:
            print(f"[SCHEDULER] Job failed: {job_id} - {e}")
            
            # Mark as failed (or retry)
            attempts = job.get("attempts", 0) + 1
            max_attempts = job.get("max_attempts", 3)
            
            if attempts >= max_attempts:
                self.client.table("scheduled_jobs").update({
                    "status": "failed",
                    "last_error": str(e)
                }).eq("id", job_id).execute()
            else:
                # Retry in 5 minutes
                retry_at = datetime.utcnow() + timedelta(minutes=5)
                self.client.table("scheduled_jobs").update({
                    "status": "pending",
                    "scheduled_for": retry_at.isoformat(),
                    "last_error": str(e),
                    "attempts": attempts
                }).eq("id", job_id).execute()
    
    async def _execute_substep_job(self, params: Dict) -> Dict:
        """Execute a substep (e.g., send reminder)"""
        
        task_id = params.get("task_id")
        substep_id = params.get("substep_id")
        
        if not task_id or not substep_id:
            return {"error": "Missing task_id or substep_id"}
        
        orchestrator = get_orchestrator()
        task = await orchestrator.get_task(task_id)
        
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        substep = next((s for s in task.substeps if s.id == substep_id), None)
        if not substep:
            return {"error": f"Substep {substep_id} not found"}
        
        # Execute the substep action
        executor = get_executor()
        
        if substep.action_type == "send_reminder":
            result = await self._send_reminder_for_substep(task, substep)
        else:
            result = await executor.execute(substep.action_type, substep.action_params)
        
        # Mark substep as completed
        await orchestrator.complete_substep(task_id, substep_id, result)
        
        return result
    
    async def _send_reminder_for_substep(self, task, substep) -> Dict:
        """Send a reminder email/notification"""
        
        executor = get_executor()
        params = substep.action_params
        
        # Get meeting details
        meeting_title = params.get("title", "Meeting")
        meeting_time = params.get("start_time", "")
        participants = params.get("participants", [])
        meeting_link = params.get("meeting_link", "")
        
        results = []
        
        for participant in participants:
            email = participant.get("email")
            name = participant.get("name", "")
            
            if email:
                # Send reminder email
                reminder_result = await executor.execute("send_email", {
                    "to": email,
                    "to_name": name,
                    "subject": f"Reminder: {meeting_title} starting soon",
                    "body": f"""
Hi {name or 'there'},

This is a reminder that your meeting "{meeting_title}" is starting soon.

Meeting Link: {meeting_link}
Time: {meeting_time}

Click the link above to join.

Best regards,
Your AI Assistant
                    """.strip()
                })
                results.append(reminder_result)
        
        return {"reminders_sent": len(results), "results": results}
    
    async def _send_reminder_job(self, params: Dict) -> Dict:
        """Send a standalone reminder"""
        
        executor = get_executor()
        
        to_email = params.get("to_email")
        subject = params.get("subject", "Reminder")
        body = params.get("body", "This is your reminder.")
        
        if not to_email:
            return {"error": "Missing to_email"}
        
        result = await executor.execute("send_email", {
            "to": to_email,
            "subject": subject,
            "body": body
        })
        
        return result
    
    async def _check_participant_job(self, params: Dict) -> Dict:
        """Check if a participant has joined a meeting"""
        
        meeting_id = params.get("meeting_id")
        
        # This would integrate with Jitsi API to check participants
        # For now, return placeholder
        return {"checked": True, "meeting_id": meeting_id}
    
    async def _check_meeting_status(self):
        """Check status of ongoing meetings"""
        
        if not self.client:
            return
        
        try:
            now = datetime.utcnow()
            
            # Get meetings that should be in progress
            # (started less than 2 hours ago, not completed)
            two_hours_ago = (now - timedelta(hours=2)).isoformat()
            
            result = self.client.table("meetings").select("*").eq(
                "status", "scheduled"
            ).lte(
                "start_time", now.isoformat()
            ).gte(
                "start_time", two_hours_ago
            ).execute()
            
            for meeting in result.data or []:
                # Check if meeting should be marked as in_progress or completed
                start_time = datetime.fromisoformat(meeting["start_time"].replace("Z", "+00:00"))
                duration = meeting.get("duration_minutes", 30)
                end_time = start_time + timedelta(minutes=duration)
                
                if now > end_time:
                    # Meeting should be completed - check with Jitsi
                    # For now, auto-complete after duration
                    await self._complete_meeting(meeting)
                elif now >= start_time:
                    # Meeting should be in progress
                    await self._mark_meeting_in_progress(meeting)
                    
        except Exception as e:
            print(f"[SCHEDULER] Error checking meetings: {e}")
    
    async def _mark_meeting_in_progress(self, meeting: Dict):
        """Mark meeting as in progress"""
        try:
            self.client.table("meetings").update({
                "status": "in_progress"
            }).eq("id", meeting["id"]).execute()
            print(f"[SCHEDULER] Meeting {meeting['id']} marked as in_progress")
        except Exception as e:
            print(f"[SCHEDULER] Error updating meeting: {e}")
    
    async def _complete_meeting(self, meeting: Dict):
        """Complete a meeting and update related task"""
        
        try:
            # Update meeting status
            self.client.table("meetings").update({
                "status": "completed",
                "end_time": datetime.utcnow().isoformat()
            }).eq("id", meeting["id"]).execute()
            
            # Find related task and complete it
            task_result = self.client.table("orchestrated_tasks").select("*").eq(
                "meeting_id", meeting["id"]
            ).execute()
            
            if task_result.data:
                task = task_result.data[0]
                orchestrator = get_orchestrator()
                
                # Complete remaining substeps
                substeps_result = self.client.table("task_substeps").select("*").eq(
                    "task_id", task["id"]
                ).in_("status", ["pending", "waiting"]).execute()
                
                for substep in substeps_result.data or []:
                    await orchestrator.complete_substep(
                        task["id"], 
                        substep["id"],
                        {"auto_completed": True, "reason": "Meeting duration elapsed"}
                    )
            
            print(f"[SCHEDULER] Meeting {meeting['id']} completed")
            
        except Exception as e:
            print(f"[SCHEDULER] Error completing meeting: {e}")


# =============================================================================
# SINGLETON
# =============================================================================

_scheduler: Optional[JobScheduler] = None

def get_scheduler() -> JobScheduler:
    """Get the singleton JobScheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler

def start_scheduler():
    """Start the job scheduler"""
    scheduler = get_scheduler()
    scheduler.start()

def stop_scheduler():
    """Stop the job scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
