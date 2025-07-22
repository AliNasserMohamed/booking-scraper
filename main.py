from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import os
from datetime import datetime
import json
import logging
import asyncio
import concurrent.futures
import threading

from database import get_db, init_db, SessionLocal
from models import Hotel, ScrapingLog, ScrapingJob
from schemas import HotelResponse, ScrapingJobResponse, ScrapingLogResponse, PaginatedResponse, ScrapingJobCreate, StatsResponse
from services.scraper_service import ScraperService
from services.database_service import DatabaseService
from services.link_scraper_service import LinkScraperService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Booking Scraper API",
    description="API for managing booking.com hotel scraping data with CSV-first approach",
    version="1.0.0"
)

# Initialize database
init_db()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
scraper_service = ScraperService()
database_service = DatabaseService()
link_scraper_service = LinkScraperService()

# Background task helper functions
async def _run_complete_scraping_task(job_id: int, update_links: bool, orchestrator):
    """Background task for complete scraping"""
    session = SessionLocal()
    try:
        # Update job status to RUNNING
        job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            job.status = "RUNNING"
            job.message = "Running complete scraping process..."
            job.progress = 0.0
            session.commit()
            logger.info(f"Job {job_id} status updated to RUNNING")
        session.close()
        
        # Run the orchestrator in a separate thread to avoid blocking the main server
        logger.info(f"Starting orchestrator for job {job_id} in thread pool")
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run the blocking orchestrator in a thread pool
            success = await loop.run_in_executor(
                executor,
                orchestrator.run_complete_scraping,
                update_links
            )
        
        # Update job status based on result
        session = SessionLocal()
        job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            if success:
                job.status = "COMPLETED"
                job.message = "Complete scraping process finished successfully"
                job.progress = 100.0
                logger.info(f"Job {job_id} completed successfully")
            else:
                job.status = "FAILED"
                job.message = "Complete scraping process failed"
                logger.error(f"Job {job_id} failed")
            session.commit()
        session.close()
        
    except Exception as e:
        logger.error(f"Error in complete scraping task {job_id}: {e}")
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.message = f"Complete scraping process failed: {str(e)}"
                session.commit()
            session.close()
        except Exception as commit_error:
            logger.error(f"Error updating job status after failure: {commit_error}")

async def _run_link_scraping_task(job_id: int, orchestrator):
    """Background task for link scraping"""
    session = SessionLocal()
    try:
        # Update job status to RUNNING
        job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            job.status = "RUNNING"
            job.message = "Running link scraping process..."
            job.progress = 0.0
            session.commit()
            logger.info(f"Job {job_id} status updated to RUNNING")
        session.close()
        
        # Run the orchestrator in a separate thread to avoid blocking the main server
        logger.info(f"Starting link scraping for job {job_id} in thread pool")
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run the blocking orchestrator in a thread pool
            success = await loop.run_in_executor(
                executor,
                orchestrator.run_link_scraping,
                True  # force_update=True
            )
        
        # Update job status based on result
        session = SessionLocal()
        job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            if success:
                job.status = "COMPLETED"
                job.message = "Link scraping process finished successfully"
                job.progress = 100.0
                logger.info(f"Job {job_id} completed successfully")
            else:
                job.status = "FAILED"
                job.message = "Link scraping process failed"
                logger.error(f"Job {job_id} failed")
            session.commit()
        session.close()
        
    except Exception as e:
        logger.error(f"Error in link scraping task {job_id}: {e}")
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.message = f"Link scraping process failed: {str(e)}"
                session.commit()
            session.close()
        except Exception as commit_error:
            logger.error(f"Error updating job status after failure: {commit_error}")

async def _run_hotel_scraping_task(job_id: int, orchestrator):
    """Background task for hotel data scraping"""
    session = SessionLocal()
    try:
        # Update job status to RUNNING
        job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            job.status = "RUNNING"
            job.message = "Running hotel data scraping process..."
            job.progress = 0.0
            session.commit()
            logger.info(f"Job {job_id} status updated to RUNNING")
        session.close()
        
        # Run the orchestrator in a separate thread to avoid blocking the main server
        logger.info(f"Starting hotel scraping for job {job_id} in thread pool")
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run the blocking orchestrator in a thread pool
            success = await loop.run_in_executor(
                executor,
                orchestrator.run_hotel_scraping
            )
        
        # Update job status based on result
        session = SessionLocal()
        job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            if success:
                job.status = "COMPLETED"
                job.message = "Hotel data scraping process finished successfully"
                job.progress = 100.0
                logger.info(f"Job {job_id} completed successfully")
            else:
                job.status = "FAILED"
                job.message = "Hotel data scraping process failed"
                logger.error(f"Job {job_id} failed")
            session.commit()
        session.close()
        
    except Exception as e:
        logger.error(f"Error in hotel scraping task {job_id}: {e}")
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.message = f"Hotel data scraping process failed: {str(e)}"
                session.commit()
            session.close()
        except Exception as commit_error:
            logger.error(f"Error updating job status after failure: {commit_error}")

@app.get("/")
async def dashboard():
    """Serve the dashboard HTML page"""
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/hotels")
async def get_hotels(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in hotel title or address"),
    db: Session = Depends(get_db)
):
    """Get paginated list of hotels in the exact format requested"""
    try:
        query = db.query(Hotel)
        
        # Apply search filter
        if search:
            query = query.filter(
                (Hotel.title.ilike(f"%{search}%")) |
                (Hotel.address.ilike(f"%{search}%"))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        hotels = query.offset((page - 1) * size).limit(size).all()
        
        # Format response in the exact JSON structure requested
        hotel_list = []
        for hotel in hotels:
            hotel_dict = {
                "title": hotel.title,
                "address": hotel.address,
                "region": hotel.region,
                "postalCode": hotel.postalCode,
                "addressCountry": hotel.addressCountry,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
                "description": hotel.description,
                "stars": hotel.stars,
                "image_links": hotel.image_links or [],
                "most_famous_facilities": hotel.most_famous_facilities or {},
                "all_facilities": hotel.all_facilities or {},
                "rooms": hotel.rooms or [],
                "rating_value": hotel.rating_value,
                "rating_text": hotel.rating_text,
                "url": hotel.url
            }
            hotel_list.append(hotel_dict)
        
        # Return paginated response
        return {
            "items": hotel_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
        
    except Exception as e:
        logger.error(f"Error getting hotels: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/hotels/{hotel_id}")
async def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    """Get specific hotel by ID"""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Format response in the exact JSON structure requested
    hotel_dict = {
        "title": hotel.title,
        "address": hotel.address,
        "region": hotel.region,
        "postalCode": hotel.postalCode,
        "addressCountry": hotel.addressCountry,
        "latitude": hotel.latitude,
        "longitude": hotel.longitude,
        "description": hotel.description,
        "stars": hotel.stars,
        "image_links": hotel.image_links or [],
        "most_famous_facilities": hotel.most_famous_facilities or {},
        "all_facilities": hotel.all_facilities or {},
        "rooms": hotel.rooms or [],
        "rating_value": hotel.rating_value,
        "rating_text": hotel.rating_text,
        "url": hotel.url
    }
    
    return hotel_dict

@app.post("/api/scraping-jobs/start")
async def start_scraping_job(
    job_request: ScrapingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new scraping job with CSV-first approach"""
    try:
        # Create new job
        job = ScrapingJob(
            status="PENDING",
            urls_count=len(job_request.urls),
            message="Job created - will scrape to CSV first, then import to database"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Start background task using async wrapper
        async def run_scraping_job_async():
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    scraper_service.run_scraping_job,
                    job.id,
                    job_request.urls
                )
        
        background_tasks.add_task(run_scraping_job_async)
        
        return {
            "message": "Scraping job started with CSV-first approach", 
            "job_id": job.id,
            "workflow": "Data will be saved to CSV first, then imported to database"
        }
        
    except Exception as e:
        logger.error(f"Error starting scraping job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/csv/import")
async def import_csv_to_database(
    csv_file: str = Query(..., description="Path to CSV file to import"),
    background_tasks: BackgroundTasks = None
):
    """Import CSV file to database"""
    try:
        if not os.path.exists(csv_file):
            raise HTTPException(status_code=404, detail="CSV file not found")
        
        # Run import in background if requested
        if background_tasks:
            background_tasks.add_task(scraper_service.import_csv_to_database, csv_file)
            return {"message": "CSV import started in background", "csv_file": csv_file}
        else:
            # Run import immediately
            result = scraper_service.import_csv_to_database(csv_file)
            return result
        
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/csv/upload")
async def upload_csv_file(file: UploadFile = File(...)):
    """Upload CSV file for later import"""
    try:
        # Ensure upload directory exists
        upload_dir = "data/csv/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "message": "CSV file uploaded successfully",
            "file_path": file_path,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Error uploading CSV file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/csv/files")
async def get_csv_files():
    """Get list of available CSV files"""
    try:
        csv_files = scraper_service.get_csv_files()
        return {
            "csv_files": csv_files,
            "count": len(csv_files)
        }
    except Exception as e:
        logger.error(f"Error getting CSV files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/scraping-jobs", response_model=PaginatedResponse[ScrapingJobResponse])
async def get_scraping_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated list of scraping jobs"""
    try:
        query = db.query(ScrapingJob).order_by(desc(ScrapingJob.created_at))
        total = query.count()
        jobs = query.offset((page - 1) * size).limit(size).all()
        
        # Log running jobs for debugging
        running_jobs = [job for job in jobs if job.status == "RUNNING"]
        if running_jobs:
            logger.info(f"Found {len(running_jobs)} running jobs: {[f'ID:{job.id} Status:{job.status}' for job in running_jobs]}")
        
        return PaginatedResponse(
            items=jobs,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        logger.error(f"Error getting scraping jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/scraping-jobs/{job_id}", response_model=ScrapingJobResponse)
async def get_scraping_job(job_id: int, db: Session = Depends(get_db)):
    """Get specific scraping job"""
    job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/scraping-jobs/{job_id}/stop")
async def stop_scraping_job(job_id: int, db: Session = Depends(get_db)):
    """Stop a running scraping job"""
    job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "RUNNING":
        success = scraper_service.stop_job(job_id)
        if success:
            return {"message": "Job stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop job")
    else:
        raise HTTPException(status_code=400, detail="Job is not running")

@app.post("/api/orchestrator/complete-scraping")
async def start_complete_scraping(
    update_links: bool = Query(False, description="Force update hotel links"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Start complete scraping process (links + hotel data)"""
    try:
        # Check if there's already a running job
        running_job = db.query(ScrapingJob).filter(ScrapingJob.status == "RUNNING").first()
        if running_job:
            raise HTTPException(status_code=400, detail="Another scraping job is already running")
        
        # Create orchestrator job
        from services.main_scraper_orchestrator import MainScraperOrchestrator
        orchestrator = MainScraperOrchestrator()
        
        # Create job record
        job = ScrapingJob(
            status="PENDING",
            urls_count=0,
            message=f"Complete scraping process started (update_links={update_links})",
            progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job {job.id} with status PENDING")
        
        # Start background task
        if background_tasks:
            background_tasks.add_task(
                _run_complete_scraping_task,
                job.id,
                update_links,
                orchestrator
            )
        
        return {
            "message": "Complete scraping process started",
            "job_id": job.id,
            "update_links": update_links
        }
        
    except Exception as e:
        logger.error(f"Error starting complete scraping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/orchestrator/link-scraping")
async def start_link_scraping(
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Start link scraping only"""
    try:
        # Check if there's already a running job
        running_job = db.query(ScrapingJob).filter(ScrapingJob.status == "RUNNING").first()
        if running_job:
            raise HTTPException(status_code=400, detail="Another scraping job is already running")
        
        from services.main_scraper_orchestrator import MainScraperOrchestrator
        orchestrator = MainScraperOrchestrator()
        
        # Create job record
        job = ScrapingJob(
            status="PENDING",
            urls_count=0,
            message="Link scraping process started",
            progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job {job.id} with status PENDING")
        
        # Start background task
        if background_tasks:
            background_tasks.add_task(
                _run_link_scraping_task,
                job.id,
                orchestrator
            )
        
        return {
            "message": "Link scraping process started",
            "job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"Error starting link scraping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/orchestrator/hotel-scraping")
async def start_hotel_scraping(
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Start hotel data scraping from existing CSV"""
    try:
        # Check if there's already a running job
        running_job = db.query(ScrapingJob).filter(ScrapingJob.status == "RUNNING").first()
        if running_job:
            raise HTTPException(status_code=400, detail="Another scraping job is already running")
        
        from services.main_scraper_orchestrator import MainScraperOrchestrator
        orchestrator = MainScraperOrchestrator()
        
        # Create job record
        job = ScrapingJob(
            status="PENDING",
            urls_count=0,
            message="Hotel data scraping process started",
            progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job {job.id} with status PENDING")
        
        # Start background task
        if background_tasks:
            background_tasks.add_task(
                _run_hotel_scraping_task,
                job.id,
                orchestrator
            )
        
        return {
            "message": "Hotel data scraping process started",
            "job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"Error starting hotel scraping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/orchestrator/complete-scraping-force")
async def start_complete_scraping_force(
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Start complete scraping process with forced link update"""
    try:
        # Check if there's already a running job
        running_job = db.query(ScrapingJob).filter(ScrapingJob.status == "RUNNING").first()
        if running_job:
            raise HTTPException(status_code=400, detail="Another scraping job is already running")
        
        from services.main_scraper_orchestrator import MainScraperOrchestrator
        orchestrator = MainScraperOrchestrator()
        
        # Create job record
        job = ScrapingJob(
            status="PENDING",
            urls_count=0,
            message="Complete scraping process started (force link update)",
            progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job {job.id} with status PENDING")
        
        # Start background task
        if background_tasks:
            background_tasks.add_task(
                _run_complete_scraping_task,
                job.id,
                True,  # Force update links
                orchestrator
            )
        
        return {
            "message": "Complete scraping process started (force link update)",
            "job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"Error starting complete scraping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/export/hotels")
async def export_hotels(db: Session = Depends(get_db)):
    """Export all hotels to CSV"""
    try:
        hotels = db.query(Hotel).all()
        if not hotels:
            raise HTTPException(status_code=404, detail="No hotels found")
        
        csv_path = database_service.export_hotels_to_csv(hotels)
        return FileResponse(csv_path, filename="hotels_export.csv", media_type="text/csv")
        
    except Exception as e:
        logger.error(f"Error exporting hotels: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        total_hotels = db.query(Hotel).count()
        running_jobs = db.query(ScrapingJob).filter(ScrapingJob.status == "RUNNING").count()
        failed_jobs = db.query(ScrapingJob).filter(ScrapingJob.status == "FAILED").count()
        
        logger.info(f"Stats - Total hotels: {total_hotels}, Running jobs: {running_jobs}, Failed jobs: {failed_jobs}")
        
        return StatsResponse(
            total_hotels=total_hotels,
            running_jobs=running_jobs,
            failed_jobs=failed_jobs
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/scraping/stats")
async def get_scraping_stats():
    """Get detailed scraping statistics"""
    try:
        stats = scraper_service.get_scraping_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting scraping stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/test-job")
async def create_test_job(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a test job to verify the system is working"""
    try:
        # Create a simple test job
        job = ScrapingJob(
            status="PENDING",
            urls_count=0,
            message="Test job created",
            progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created test job {job.id}")
        
        # Add a simple background task that updates the job status
        async def test_task():
            await asyncio.sleep(2)  # Wait 2 seconds
            session = SessionLocal()
            test_job = session.query(ScrapingJob).filter(ScrapingJob.id == job.id).first()
            if test_job:
                test_job.status = "RUNNING"
                test_job.message = "Test job is running"
                test_job.progress = 50.0
                session.commit()
                logger.info(f"Test job {job.id} updated to RUNNING")
            session.close()
            
            await asyncio.sleep(3)  # Wait 3 more seconds
            session = SessionLocal()
            test_job = session.query(ScrapingJob).filter(ScrapingJob.id == job.id).first()
            if test_job:
                test_job.status = "COMPLETED"
                test_job.message = "Test job completed successfully"
                test_job.progress = 100.0
                session.commit()
                logger.info(f"Test job {job.id} completed")
            session.close()
        
        background_tasks.add_task(test_task)
        
        return {
            "message": "Test job created",
            "job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"Error creating test job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/database/backup")
async def backup_database():
    """Backup database to CSV"""
    try:
        backup_path = database_service.backup_database_to_csv()
        return {
            "message": "Database backup completed",
            "backup_path": backup_path
        }
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/database/reset")
async def reset_database(db: Session = Depends(get_db)):
    """Reset database (WARNING: This will delete all data)"""
    try:
        from database import reset_database
        reset_database()
        return {"message": "Database reset completed"}
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 