# from apscheduler.schedulers.background import BackgroundScheduler

# # from apscheduler.triggers.cron import CronTrigger
# from fastapi import FastAPI
# from contextlib import asynccontextmanager
# from datetime import datetime, timedelta, date
# import logging
# from typing import AsyncGenerator

# from ..database import get_db
# from ..arrangements import services
# from ..arrangements.commons.dataclasses import UpdateArrangementRequest
# from .commons.models import LatestArrangement
# from .commons.enums import Action, ApprovalStatus

# # Configure logging with more details
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger(__name__)

# # Initialize scheduler
# scheduler = BackgroundScheduler()


# @asynccontextmanager
# async def get_db_context() -> AsyncGenerator:
#     """Context manager for database session handling."""
#     db = next(get_db())
#     try:
#         yield db
#     finally:
#         db.close()


# def get_tomorrow_date() -> date:
#     """Get tomorrow's date at midnight."""
#     return datetime.now().date() + timedelta(days=1)


# async def process_single_request(db, request, system_approver_id: int) -> bool:
#     """Process a single WFH request. Returns True if successful, False otherwise."""
#     try:
#         wfh_update = UpdateArrangementRequest(
#             arrangement_id=request.arrangement_id.value,
#             update_datetime=datetime.now(),
#             action=Action.REJECT,
#             approving_officer=system_approver_id,
#             status_reason="Auto-rejected due to pending status one day before WFH date",
#             supporting_doc_1=None,
#             supporting_doc_2=None,
#             supporting_doc_3=None,
#         )

#         await services.update_arrangement_approval_status(
#             db=db,
#             wfh_update=wfh_update,
#             supporting_docs=[],
#         )

#         logger.info(
#             f"Auto-rejected arrangement {request.arrangement_id} for date {request.wfh_date}"
#         )
#         return True

#     except Exception as e:
#         logger.error(
#             f"Error processing arrangement {request.arrangement_id}: {str(e)}", exc_info=True
#         )
#         return False


# async def auto_reject_old_requests():
#     """Automatically reject WFH requests that are still pending one day before the WFH date."""
#     async with get_db_context() as db:
#         try:
#             tomorrow = get_tomorrow_date()

#             # Query for pending WFH requests
#             wfh_requests = (
#                 db.query(LatestArrangement)
#                 .filter(
#                     LatestArrangement.current_approval_status == ApprovalStatus.PENDING_APPROVAL,
#                     LatestArrangement.wfh_date == tomorrow.strftime("%Y-%m-%d"),
#                 )
#                 .all()
#             )

#             if not wfh_requests:
#                 logger.info("No pending WFH requests found for auto-rejection")
#                 return

#             logger.info(f"Found {len(wfh_requests)} pending requests to process")

#             system_approver_id = 1  # TODO: Make this configurable via env variable

#             success_count = 0
#             for request in wfh_requests:
#                 if await process_single_request(db, request, system_approver_id):
#                     success_count += 1

#             # Only commit if we processed any requests successfully
#             if success_count > 0:
#                 db.commit()
#                 logger.info(f"Successfully processed {success_count}/{len(wfh_requests)} requests")
#             else:
#                 logger.warning("No requests were processed successfully")
#                 db.rollback()

#         except Exception as e:
#             logger.error(f"Error in auto_reject_old_requests: {str(e)}", exc_info=True)
#             db.rollback()
#             raise  # Re-raise to ensure the scheduler logs the error


# # @asynccontextmanager
# # async def lifespan(app: FastAPI):
# #     """Lifecycle management for the FastAPI application."""
# #     try:
# #         # Start scheduler
# #         scheduler.add_job(
# #             auto_reject_old_requests,
# #             CronTrigger(hour=0, minute=0),
# #             id="auto_reject_job",
# #             replace_existing=True,
# #             misfire_grace_time=300,  # 5 minutes grace time
# #             max_instances=1,  # Ensure only one instance runs at a time
# #         )
# #         scheduler.start()
# #         logger.info("Scheduler started successfully")

# #         yield

# #     except Exception as e:
# #         logger.error(f"Error in scheduler lifecycle: {str(e)}", exc_info=True)
# #         raise
# #     finally:
# #         scheduler.shutdown(wait=True)  # Changed to wait=True for clean shutdown
# #         logger.info("Scheduler shutdown completed")
