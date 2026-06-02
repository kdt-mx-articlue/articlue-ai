import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector.similarity_service import search_similar_jobs

def main():
    query = "Python FastAPI AI backend 개발"

    results = search_similar_jobs(query)

    for r in results:
        print(r)

if __name__ == "__main__":
    main()