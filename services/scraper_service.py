import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from models import ScrapingJob, ScrapingLog
from database import SessionLocal
from services.database_service import DatabaseService
from services.BookingHotelsScraper import BookingScraperIntegration

logger = logging.getLogger(__name__)

class ScraperService:
    """Service for managing scraping jobs and integrating with BookingHotelsScraper"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        self.current_job_id: int = None
        self.booking_scraper = None
    
    def _update_job_status(self, job_id: int, status: str, progress: float = 0, message: str = ""):
        """Update job status in database"""
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job:
                job.status = status
                job.progress = progress
                job.message = message
                job.updated_at = datetime.utcnow()
                session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
    
    def _update_job_progress(self, job_id: int, progress: float, message: str = ""):
        """Update job progress"""
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job:
                job.progress = progress
                job.message = message
                job.updated_at = datetime.utcnow()
                session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error updating job progress: {str(e)}")
    
    def _log_message(self, message: str, level: str = "INFO"):
        """Log message to database and console"""
        try:
            logger.log(getattr(logging, level), message)
            if self.current_job_id:
                self.database_service.save_scraping_log(message, level, self.current_job_id)
        except Exception as e:
            logger.error(f"Error logging message: {str(e)}")
    
    def run_scraping_job(self, job_id: int, urls: List[str]):
        """Run a complete scraping job using BookingHotelsScraper with CSV-first approach"""
        self.current_job_id = job_id
        
        try:
            self._log_message(f"Starting scraping job {job_id} with {len(urls)} URLs", "INFO")
            self._update_job_status(job_id, "RUNNING", 0, "Starting scraping process...")
            
            # Initialize BookingHotelsScraper
            self.booking_scraper = BookingScraperIntegration()
            
            # Run the scraping process (CSV first, then database)
            result = self.booking_scraper.run_scraping(urls=urls, job_id=job_id)
            
            if result.get("success"):
                # Update job with success status
                progress = 100.0
                success_message = f"Completed: {result.get('scraped_count', 0)} scraped, {result.get('imported_count', 0)} imported"
                
                self._update_job_status(job_id, "COMPLETED", progress, success_message)
                self._log_message(f"Job {job_id} completed successfully: {success_message}", "INFO")
                
                # Update job counters
                session = SessionLocal()
                job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
                if job:
                    job.scraped_count = result.get('scraped_count', 0)
                    job.failed_count = result.get('failed_count', 0)
                    session.commit()
                session.close()
                
            else:
                # Update job with failure status
                error_message = result.get("message", "Unknown error")
                self._update_job_status(job_id, "FAILED", 0, error_message)
                self._log_message(f"Job {job_id} failed: {error_message}", "ERROR")
                
        except Exception as e:
            error_message = f"Scraping job failed: {str(e)}"
            self._update_job_status(job_id, "FAILED", 0, error_message)
            self._log_message(error_message, "ERROR")
            raise
        
        finally:
            # Clean up
            if self.booking_scraper:
                self.booking_scraper.close()
            self.current_job_id = None
    
    def import_csv_to_database(self, csv_file: str) -> Dict[str, Any]:
        """Import CSV file to database"""
        try:
            self._log_message(f"Importing CSV file to database: {csv_file}", "INFO")
            
            # Use database service to import
            imported_count = self.database_service.import_hotels_from_csv(csv_file)
            
            result = {
                "success": True,
                "message": f"Successfully imported {imported_count} hotels",
                "imported_count": imported_count
            }
            
            self._log_message(f"CSV import completed: {imported_count} hotels imported", "INFO")
            return result
            
        except Exception as e:
            error_message = f"CSV import failed: {str(e)}"
            self._log_message(error_message, "ERROR")
            return {"success": False, "message": error_message}
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        try:
            if self.booking_scraper:
                return self.booking_scraper.get_stats()
            else:
                # Initialize temporary scraper to get stats
                temp_scraper = BookingScraperIntegration()
                stats = temp_scraper.get_stats()
                temp_scraper.close()
                return stats
        except Exception as e:
            logger.error(f"Error getting scraping stats: {str(e)}")
            return {}
    
    def get_csv_files(self) -> List[str]:
        """Get list of available CSV files"""
        try:
            temp_scraper = BookingScraperIntegration()
            csv_files = temp_scraper.get_csv_files()
            temp_scraper.close()
            return csv_files
        except Exception as e:
            logger.error(f"Error getting CSV files: {str(e)}")
            return []
    
    def stop_job(self, job_id: int) -> bool:
        """Stop a running scraping job"""
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job and job.status == "RUNNING":
                job.status = "STOPPED"
                job.message = "Job stopped by user"
                job.updated_at = datetime.utcnow()
                session.commit()
                session.close()
                
                self._log_message(f"Job {job_id} stopped by user", "INFO")
                return True
            else:
                session.close()
                return False
        except Exception as e:
            logger.error(f"Error stopping job: {str(e)}")
            return False
    
    def cleanup_old_jobs(self, days: int = 30):
        """Clean up old completed/failed jobs"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            session = SessionLocal()
            old_jobs = session.query(ScrapingJob).filter(
                ScrapingJob.created_at < cutoff_date,
                ScrapingJob.status.in_(["COMPLETED", "FAILED", "STOPPED"])
            ).all()
            
            for job in old_jobs:
                session.delete(job)
            
            session.commit()
            session.close()
            
            self._log_message(f"Cleaned up {len(old_jobs)} old jobs", "INFO")
            return len(old_jobs)
            
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {str(e)}")
            return 0 