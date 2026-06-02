from app.services.vector.job_vector_service import save_jobs
from app.services.vector.resume_vector_service import save_resume


# =========================
# VECTOR ENTRY POINT
# =========================
def save_to_vector_db(candidate_data, jobs_data):

    save_jobs(jobs_data)
    save_resume(candidate_data)