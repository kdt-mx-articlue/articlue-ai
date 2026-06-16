from app.services.vector.job_vector_service import save_jobs
from app.services.vector.resume_vector_service import save_resume
from app.services.vector.utils import prepare_candidate_data


def save_to_vector_db(candidate_data, jobs_data):

    # 1) job 저장
    save_jobs(jobs_data)

    # 2) resume 데이터 안전 변환 (flatten 포함)
    safe_candidate_data = prepare_candidate_data(candidate_data)

    # 3) resume 저장
    save_resume(safe_candidate_data)