from mcp.server.fastmcp import FastMCP

from . import api
from .logger import logger

mcp = FastMCP("moodle-mcp", dependencies=["glom", "requests"])


@mcp.tool()
def get_upcoming_events() -> list[api.UpcomingEvent]:
    """Get upcoming events from moodle"""
    return api.get_upcoming_events()


@mcp.tool()
def get_my_courses() -> list[api.Course]:
    """Get all courses the current user is enrolled in"""
    return api.get_my_courses()


@mcp.tool()
def get_course_content(courseid: int) -> list[api.CourseSection]:
    """Get sections and modules for a specific course by its ID"""
    return api.get_course_content(courseid)


@mcp.tool()
def get_assignments(
    courseids: list[int] | None = None,
    my_class: str | None = None,
    filter_by_class: bool = True,
) -> list[api.Assignment]:
    """Get assignments for courses, automatically filtered to the student's class.

    By default only returns assignments that belong to this student's class slot
    (e.g. 'Pagi C') or have no class tag. Assignments for 'Pagi A', 'Malam B', etc.
    are hidden unless ``filter_by_class=False``.

    Parameters
    ----------
    courseids: optional list of course IDs to restrict the query.
    my_class: override the class slot (e.g. 'Pagi C'). Default: MOODLE_MY_CLASS env.
    filter_by_class: set False to see all assignments including other classes.
    """
    return api.get_assignments(courseids, my_class=my_class, filter_by_class=filter_by_class)


@mcp.tool()
def get_assignment_status(assignid: int) -> api.AssignmentStatus:
    """Get submission and grading status for a specific assignment by its ID"""
    return api.get_assignment_status(assignid)


@mcp.tool()
def get_upcoming_deadlines() -> list[api.UpcomingDeadline]:
    """Get upcoming assignment deadlines across all courses, sorted by due date"""
    return api.get_upcoming_deadlines()


@mcp.tool()
def get_grades(courseid: int | None = None) -> list[api.CourseGrade] | list[api.GradeItem]:
    """Get grade overview for all courses, or detailed grades for a specific course if courseid is provided"""
    return api.get_grades(courseid)


@mcp.tool()
def search_course_materials(query: str) -> list[api.SearchResult]:
    """Search across all course materials by query string"""
    return api.search_course_materials(query)


@mcp.tool()
def semester_dashboard() -> api.SemesterDashboard:
    """Get an aggregated overview combining courses, upcoming deadlines, and grades"""
    return api.semester_dashboard()


@mcp.tool()
def get_actionable_tasks() -> list[api.ActionableTask]:
    """Returns prioritized list of tasks needing action, sorted by urgency (overdue first)"""
    return api.get_actionable_tasks()


@mcp.tool()
def get_overdue_assignments() -> list[api.OverdueAssignment]:
    """Returns assignments past due date that are unsubmitted, sorted by most overdue first"""
    return api.get_overdue_assignments()


@mcp.tool()
def get_recent_activity(since: int | None = None) -> list[api.RecentActivity]:
    """Returns recent activity/updates across courses. Optionally specify 'since' as Unix timestamp (defaults to 7 days ago)"""
    return api.get_recent_activity(since)


@mcp.tool()
def get_course_announcements(courseid: int | None = None) -> list[api.CourseAnnouncement]:
    """Gets announcements from course news forums. Optionally filter by course ID"""
    return api.get_course_announcements(courseid)


@mcp.tool()
def get_course_health(courseid: int) -> api.CourseHealth:
    """Overall health check for a course: progress, grades, unsubmitted/overdue counts"""
    return api.get_course_health(courseid)


@mcp.tool()
def get_course_progress(courseid: int | None = None) -> list[api.CourseProgress]:
    """Progress/completion for courses. Optionally specify a course ID, or get all courses"""
    return api.get_course_progress(courseid)


@mcp.tool()
def get_study_load() -> api.StudyLoad:
    """Study load analysis showing assignment distribution by week, identifying heavy weeks"""
    return api.get_study_load()


@mcp.tool()
def daily_briefing() -> api.DailyBriefing:
    """Aggregated daily summary: overdue count, today's deadlines, recent grades, upcoming events, actionable tasks"""
    return api.daily_briefing()


@mcp.tool()
def weekly_review() -> api.WeeklyReview:
    """Aggregated weekly summary: submitted/graded counts, upcoming deadlines, overdue count, progress"""
    return api.weekly_review()


@mcp.tool()
def detect_new_assignments(update_state: bool = True) -> api.AssignmentDiffReport:
    """Detect new assignments, removed assignments, and deadline changes since the previous snapshot."""
    return api.detect_new_assignments(update_state=update_state)


@mcp.tool()
def detect_grade_changes(update_state: bool = True) -> api.GradeDiffReport:
    """Detect newly visible, changed, and removed course grades since the previous snapshot."""
    return api.detect_grade_changes(update_state=update_state)


@mcp.tool()
def deadline_watchdog(days_ahead: int = 3) -> api.DeadlineWatchdogReport:
    """Return unsubmitted assignment deadlines within the next N days for alerting."""
    return api.deadline_watchdog(days_ahead=days_ahead)


@mcp.tool()
def sync_moodle_to_obsidian(target_dir: str | None = None, include_course_materials: bool = True) -> api.ObsidianSyncResult:
    """Sync Moodle dashboard, deadlines, grades, and course notes to Obsidian Academic/Moodle."""
    return api.sync_moodle_to_obsidian(target_dir=target_dir, include_course_materials=include_course_materials)


@mcp.tool()
def export_deadlines_to_obsidian(target_dir: str | None = None) -> api.ObsidianSyncResult:
    """Export Moodle deadlines to Obsidian Academic/Moodle/Deadlines.md."""
    return api.export_deadlines_to_obsidian(target_dir=target_dir)


@mcp.tool()
def export_course_outline(courseid: int, target_dir: str | None = None) -> api.ObsidianSyncResult:
    """Export one Moodle course outline/material list to Obsidian Academic/Moodle/Courses."""
    return api.export_course_outline(courseid=courseid, target_dir=target_dir)


@mcp.tool()
def list_course_material_files(courseid: int) -> list[api.DownloadableFile]:
    """List downloadable files exposed by a course's content modules."""
    return api.list_course_material_files(courseid)


@mcp.tool()
def download_course_materials(courseid: int, target_dir: str | None = None, overwrite: bool = False) -> api.DownloadReport:
    """Download all file materials from a Moodle course into Academic/Moodle/Materials."""
    return api.download_course_materials(courseid=courseid, target_dir=target_dir, overwrite=overwrite)


@mcp.tool()
def download_assignment_attachments(assignid: int, target_dir: str | None = None, overwrite: bool = False) -> api.DownloadReport:
    """Download intro attachments for a Moodle assignment into Academic/Moodle/Materials/Assignments."""
    return api.download_assignment_attachments(assignid=assignid, target_dir=target_dir, overwrite=overwrite)


# ---------------------------------------------------------------------------
# Phase 4 — Assignment submission tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_submission_status_detail(assignid: int) -> api.SubmissionStatusDetail:
    """Get detailed submission status for an assignment: state, grading status, submitted files, and edit permissions."""
    return api.get_submission_status_detail(assignid=assignid)


@mcp.tool()
def submit_assignment_text(assignid: int, text: str, format: int = 1) -> api.SubmissionResult:
    """Submit an online text answer for a Moodle assignment. format: 1=HTML (default), 0=MOODLE, 2=PLAIN."""
    return api.submit_assignment_text(assignid=assignid, text=text, format=format)


@mcp.tool()
def get_assignment_feedback(assignid: int) -> api.AssignmentFeedback:
    """Get the grade and feedback comments left by the grader for an assignment."""
    return api.get_assignment_feedback(assignid=assignid)


# ---------------------------------------------------------------------------
# Phase 6 — Calendar & Completion tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_calendar_event(
    name: str,
    timestart: int,
    eventtype: str = "user",
    description: str = "",
    timeduration: int = 0,
    courseid: int | None = None,
) -> api.CalendarEvent:
    """Create a new personal or course event in the Moodle calendar. timestart is a Unix timestamp."""
    return api.create_calendar_event(
        name=name, timestart=timestart, eventtype=eventtype,
        description=description, timeduration=timeduration, courseid=courseid,
    )


@mcp.tool()
def get_activity_completion(courseid: int) -> list[api.ActivityCompletionStatus]:
    """Get completion status (done/not done) for every activity in a course."""
    return api.get_activity_completion(courseid=courseid)


@mcp.tool()
def mark_activity_complete(cmid: int, completed: bool = True) -> api.CompletionUpdateResult:
    """Manually mark a course activity as complete or incomplete (only works for manual-completion activities)."""
    return api.mark_activity_complete(cmid=cmid, completed=completed)


@mcp.tool()
def get_course_updates(courseid: int, since: int | None = None) -> list[api.CourseUpdateInstance]:
    """Get module-level changes in a course since a timestamp (default: last 24 hours)."""
    return api.get_course_updates(courseid=courseid, since=since)


@mcp.tool()
def ask_moodle(question: str) -> api.MoodleAnswer:
    """Ask a natural language question about your Moodle data. Routes to the right data sources based on your question"""
    return api.ask_moodle(question)


@mcp.tool()
def analyze_assignment(assignid: int) -> api.AssignmentAnalysis:
    """Comprehensive analysis of an assignment: status, requirements, materials count, course progress, and deadline info"""
    return api.analyze_assignment(assignid)


@mcp.tool()
def extract_assignment_requirements(assignid: int) -> api.AssignmentRequirements:
    """Extract and structure requirements, deliverables, constraints, and evaluation criteria from an assignment description"""
    return api.extract_assignment_requirements(assignid)


@mcp.tool()
def find_relevant_materials(assignid: int) -> api.RelevantMaterials:
    """Find course content and search results relevant to a specific assignment, ranked by relevance"""
    return api.find_relevant_materials(assignid)


@mcp.tool()
def decompose_task(assignid: int) -> api.TaskDecomposition:
    """Break down an assignment into subtasks with estimated effort, dependencies, and critical path"""
    return api.decompose_task(assignid)


@mcp.tool()
def create_implementation_plan(assignid: int) -> api.ImplementationPlan:
    """Create a step-by-step implementation plan for completing an assignment, with timeline, resources, milestones, and risk factors"""
    return api.create_implementation_plan(assignid)


def main():
    logger.info("Starting moodle-mcp server")
    mcp.run()