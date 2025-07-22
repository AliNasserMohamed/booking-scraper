import requests
import json
import csv
import time
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session

from services.database_service import DatabaseService
from models import ScrapingJob
from database import SessionLocal

# Setup logging with custom format (no timestamps)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('link_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
Sorterings=["distance_from_search","popularity","class","upsort_bh","price_from_high_to_low","class_asc","bayesian_review_score"]


class LinkScraperService:
    """Service for scraping booking.com hotel links from cities"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        self.current_job_id = None
        self.scrapped_links: Set[str] = set()
        
    def _log_message(self, message: str, level: str = "INFO", hotel_id: Optional[int] = None):
        """Log message to database and console"""
        try:
            # Clean message for console display
            clean_message = message.replace('\n', ' ').strip()
            print(f"[{level}] {clean_message}")
            
            # Also log to file
            logger.log(getattr(logging, level), clean_message)
            
        except Exception as e:
            print(f"[ERROR] Failed to log message: {str(e)}")
            
        # Save to database (optional)
        try:
            if hasattr(self, 'database_service'):
                self.database_service.save_scraping_log(message, level, hotel_id)
        except Exception as e:
            print(f"[WARN] Failed to save log to database: {str(e)}")
    
    def _update_job_progress(self, job_id: int, processed_urls: int, status: str = None):
        """Update job progress in database"""
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            if job:
                job.scraped_count = processed_urls
                if status:
                    job.status = status
                session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error updating job progress: {str(e)}")
            # Don't use _log_message here to avoid potential recursion
    
    def _should_stop_job(self, job_id: int) -> bool:
        """Check if job should be stopped"""
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            should_stop = job and job.status in ["STOPPED", "CANCELLED", "FAILED"]
            session.close()
            return should_stop
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return False
    
    def get_city_destination_id(self, city_name: str) -> Optional[int]:
        """Get destination ID for a city using GraphQL API"""
        try:
            url = "https://www.booking.com/dml/graphql?ss=%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6%2C+%D9%85%D9%86%D8%B7%D9%82%D8%A9+%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6%2C+%D8%A7%D9%84%D9%85%D9%85%D9%84%D9%83%D8%A9+%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9&ssne=%D8%A7%D9%84%D9%82%D8%A7%D9%87%D8%B1%D8%A9&ssne_untouched=%D8%A7%D9%84%D9%82%D8%A7%D9%87%D8%B1%D8%A9&highlighted_hotels=2021099&efdco=1&label=gen173nr-1FCAsoxAFCF2p1bWVpcmFoLXZpbGxhcy1qZWRkYWgxSAFYBGhDiAEBmAEBuAEXyAEM2AEB6AEB-AECiAIBqAIDuALqgL7DBsACAdICJDdhYzAzNWRhLTYwMjAtNDA5YS04NGFlLWIzZWYyM2MzN2EyNNgCBeACAQ&aid=304142&lang=ar&sb=1&src_elem=sb&src=searchresults&dest_id=900040280&dest_type=city&place_id=city%2F900040280&ac_position=0&ac_click_type=b&ac_langcode=ar&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=18dd66afc49fc4084e14c724527ce9b1&ac_meta=GiAxOGRkNjZhZmM0OWZjNDA4NGUxNGM3MjQ1MjdjZTliMSAAKAEyAmFyOgzYp9mE2LHZitin2LZAAEoAUAA%3D&group_adults=2&no_rooms=1&group_children=0"

            payload = json.dumps({
                "operationName": "AutoComplete",
                "variables": {
                    "input": {
                        "prefixQuery": city_name,
                        "nbSuggestions": 1,
                        "fallbackConfig": {
                            "mergeResults": True,
                            "nbMaxMergedResults": 6,
                            "nbMaxThirdPartyResults": 3,
                            "sources": [
                                "GOOGLE",
                                "HERE"
                            ]
                        },
                        "requestConfig": {
                            "enableRequestContextBoost": True
                        },
                        "requestContext": {
                            "pageviewId": "cfd97a868a78f6d662dce04e9c2f00e9",
                            "location": {
                                "destId": 900040280,
                                "destType": "CITY"
                            }
                        }
                    }
                },
                "extensions": {},
                "query": "query AutoComplete($input: AutoCompleteRequestInput!) {\n  autoCompleteSuggestions(input: $input) {\n    results {\n      destination {\n        countryCode\n        destId\n        destType\n        latitude\n        longitude\n        __typename\n      }\n      displayInfo {\n        imageUrl\n        label\n        labelComponents {\n          name\n          type\n          __typename\n        }\n        showEntireHomesCheckbox\n        title\n        subTitle\n        __typename\n      }\n      metaData {\n        isSkiItem\n        langCode\n        maxLosData {\n          extendedLoS\n          __typename\n        }\n        metaMatches {\n          id\n          text\n          type\n          __typename\n        }\n        roundTrip\n        webFilters\n        autocompleteResultId\n        autocompleteResultSource\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
            })
            
            headers = {
                'accept': '*/*',
                'accept-language': 'en-GB,en;q=0.9,ar-EG;q=0.8,ar;q=0.7,en-US;q=0.6',
                'apollographql-client-name': 'b-search-web-searchresults_rust',
                'apollographql-client-version': 'ZWHCTNca',
                'content-type': 'application/json',
                'origin': 'https://www.booking.com',
                'priority': 'u=1, i',
                'referer': 'https://www.booking.com/searchresults.ar.html',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'x-booking-context-action-name': 'searchresults_irene',
                'x-booking-context-aid': '304142',
                'x-booking-csrf-token': 'eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJjb250ZXh0LWVucmljaG1lbnQtYXBpIiwic3ViIjoiY3NyZi10b2tlbiIsImlhdCI6MTc1MjE3MjMxNCwiZXhwIjoxNzUyMjU4NzE0fQ.PY5jkDyEbnMUhdlkhj3PaSNbk4-b9E_1eiCnvmU3Ew5SxeBI80t6NgE6ihW5NcQRY_c4DhZYcF9UNP1TqORcWA',
                'x-booking-dml-cluster': 'rust',
                'x-booking-et-serialized-state': 'EShdkKUUPvKAQpDdGzh5TufDe1zYllk076r7tmFIO_3I3Ac3lfc8zvyez8A3C7rxP',
                'x-booking-pageview-id': 'cfd97a868a78f6d662dce04e9c2f00e9',
                'x-booking-site-type-id': '1',
                'x-booking-topic': 'capla_browser_b-search-web-searchresults'
            }

            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("data", {}).get("autoCompleteSuggestions", {}).get("results", [])
            
            if results:
                dest_id = results[0].get("destination", {}).get("destId")
                label = results[0].get("displayInfo", {}).get("label")
                if "المملكة العربية السعودية" not in label:
                    return None
                if dest_id:
                    return int(dest_id)
            
            return None
            
        except Exception as e:
            self._log_message(f"Error getting destination ID for city {city_name}: {str(e)}", "ERROR")
            return None
    
    def scrape_city_hotels(self, city_name: str, dest_id: int, sorter: str, city_or_country: str, offset: int = 0, rows_per_page: int = 100) -> tuple:
        """Scrape hotel links for a specific city"""
        try:
            url = "https://www.booking.com/dml/graphql"
            
            payload = json.dumps({
                "operationName": "FullSearch",
                "variables": {
                    "includeBundle": False,
                    "input": {
                        "acidCarouselContext": None,
                        "childrenAges": [],
                        "doAvailabilityCheck": False,
                        "encodedAutocompleteMeta": None,
                        "enableCampaigns": True,
                        "filters": {},
                        "flexibleDatesConfig": {
                            "broadDatesCalendar": {
                                "checkinMonths": [
                                    ""
                                ],
                                "los": [],
                                "startWeekdays": []
                            },
                            "dateFlexUseCase": "DATE_RANGE",
                            "dateRangeCalendar": {
                                "checkin": [],
                                "checkout": []
                            }
                        },
                        "forcedBlocks": None,
                        "location": {
                            "searchString": city_name,
                            "topUfis": True,
                            "destType": city_or_country,
                            "destId": dest_id
                        },
                        "metaContext": {
                            "metaCampaignId": 0,
                            "externalTotalPrice": None,
                            "feedPrice": None,
                            "hotelCenterAccountId": None,
                            "rateRuleId": None,
                            "dragongateTraceId": None,
                            "pricingProductsTag": None
                        },
                        "nbRooms": 1,
                        "nbAdults": 2,
                        "nbChildren": 0,
                        "showAparthotelAsHotel": True,
                        "needsRoomsMatch": False,
                        "optionalFeatures": {
                            "forceArpExperiments": True,
                            "testProperties": False
                        },
                        "pagination": {
                            "rowsPerPage": rows_per_page,
                            "offset": offset
                        },
                        "rawQueryForSession": "/searchresults.ar.html?label=gen173nr-1FCAsoxAFCF2p1bWVpcmFoLXZpbGxhcy1qZWRkYWgxSAFYBGhDiAEBmAEBuAEXyAEM2AEB6AEB-AECiAIBqAIDuALqgL7DBsACAdICJDdhYzAzNWRhLTYwMjAtNDA5YS04NGFlLWIzZWYyM2MzN2EyNNgCBeACAQ&sid=8ce98259cec3d26db7ed7c72f78462e3&aid=304142&ss=%D8%A7%D9%84%D9%85%D9%85%D9%84%D9%83%D8%A9+%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9&ssne=%D8%A7%D9%84%D9%85%D9%85%D9%84%D9%83%D8%A9+%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9&ssne_untouched=%D8%A7%D9%84%D9%85%D9%85%D9%84%D9%83%D8%A9+%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9&efdco=1&lang=ar&sb=1&src_elem=sb&src=searchresults&dest_id=186&dest_type=country&ltfd=%3A%3A%3A%3A&group_adults=2&no_rooms=1&group_children=0",
                        "referrerBlock": {
                            "blockName": "searchbox"
                        },
                        "sbCalendarOpen": False,
                        "sorters": {
                            "selectedSorter": sorter,
                            "referenceGeoId": None,
                            "tripTypeIntentId": None
                        },
                        "travelPurpose": 0,
                        "seoThemeIds": [
                        ],
                        "useSearchParamsFromSession": True,
                        "merchInput": {
                            "testCampaignIds": []
                        },
                        "webSearchContext": {
                            "reason": "CLIENT_SIDE_UPDATE",
                            "source": "SEARCH_RESULTS",
                            "outcome": "SEARCH_RESULTS"
                        },
                        "clientSideRequestId": "09d7d10a227948219463cd7fc6a518e1"
                    },
                    "carouselLowCodeExp": False
                },
                "extensions": {},
                        "query": "query FullSearch($input: SearchQueryInput!, $carouselLowCodeExp: Boolean!, $includeBundle: Boolean = false) {\n  searchQueries {\n    search(input: $input) {\n      ...FullSearchFragment\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FullSearchFragment on SearchQueryOutput {\n  banners {\n    ...Banner\n    __typename\n  }\n  breadcrumbs {\n    ... on SearchResultsBreadcrumb {\n      ...SearchResultsBreadcrumb\n      __typename\n    }\n    ... on LandingPageBreadcrumb {\n      ...LandingPageBreadcrumb\n      __typename\n    }\n    __typename\n  }\n  carousels {\n    ...Carousel\n    __typename\n  }\n  destinationLocation {\n    ...DestinationLocation\n    __typename\n  }\n  entireHomesSearchEnabled\n  dateFlexibilityOptions {\n    enabled\n    __typename\n  }\n  flexibleDatesConfig {\n    broadDatesCalendar {\n      checkinMonths\n      los\n      startWeekdays\n      losType\n      __typename\n    }\n    dateFlexUseCase\n    dateRangeCalendar {\n      flexWindow\n      checkin\n      checkout\n      __typename\n    }\n    __typename\n  }\n  filters {\n    ...FilterData\n    __typename\n  }\n  filtersTrackOnView {\n    type\n    experimentHash\n    value\n    __typename\n  }\n  appliedFilterOptions {\n    ...FilterOption\n    __typename\n  }\n  recommendedFilterOptions {\n    ...FilterOption\n    __typename\n  }\n  pagination {\n    nbResultsPerPage\n    nbResultsTotal\n    __typename\n  }\n  tripTypes {\n    ...TripTypesData\n    __typename\n  }\n  results {\n    ...BasicPropertyData\n    ...PropertyUspBadges\n    ...MatchingUnitConfigurations\n    ...PropertyBlocks\n    ...BookerExperienceData\n    ...TopPhotos\n    generatedPropertyTitle\n    priceDisplayInfoIrene {\n      ...PriceDisplayInfoIrene\n      __typename\n    }\n    licenseDetails {\n      nextToHotelName\n      __typename\n    }\n    isTpiExclusiveProperty\n    propertyCribsAvailabilityLabel\n    mlBookingHomeTags\n    trackOnView {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    __typename\n  }\n  searchMeta {\n    ...SearchMetadata\n    __typename\n  }\n  sorters {\n    option {\n      ...SorterFields\n      __typename\n    }\n    __typename\n  }\n  zeroResultsSection {\n    ...ZeroResultsSection\n    __typename\n  }\n  rocketmilesSearchUuid\n  previousSearches {\n    ...PreviousSearches\n    __typename\n  }\n  merchComponents {\n    ...MerchRegionIrene\n    __typename\n  }\n  wishlistData {\n    numProperties\n    __typename\n  }\n  seoThemes {\n    id\n    caption\n    __typename\n  }\n  gridViewPreference\n  advancedSearchWidget {\n    title\n    legalDisclaimer\n    description\n    placeholder\n    ctaText\n    helperText\n    __typename\n  }\n  visualFiltersGroups {\n    ...VisualFiltersGroup\n    __typename\n  }\n  __typename\n}\n\nfragment BasicPropertyData on SearchResultProperty {\n  acceptsWalletCredit\n  basicPropertyData {\n    accommodationTypeId\n    id\n    isTestProperty\n    location {\n      address\n      city\n      countryCode\n      __typename\n    }\n    pageName\n    ufi\n    photos {\n      main {\n        highResUrl {\n          relativeUrl\n          __typename\n        }\n        lowResUrl {\n          relativeUrl\n          __typename\n        }\n        highResJpegUrl {\n          relativeUrl\n          __typename\n        }\n        lowResJpegUrl {\n          relativeUrl\n          __typename\n        }\n        tags {\n          id\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    reviewScore: reviews {\n      score: totalScore\n      reviewCount: reviewsCount\n      totalScoreTextTag {\n        translation\n        __typename\n      }\n      showScore\n      secondaryScore\n      secondaryTextTag {\n        translation\n        __typename\n      }\n      showSecondaryScore\n      __typename\n    }\n    externalReviewScore: externalReviews {\n      score: totalScore\n      reviewCount: reviewsCount\n      showScore\n      totalScoreTextTag {\n        translation\n        __typename\n      }\n      __typename\n    }\n    starRating {\n      value\n      symbol\n      caption {\n        translation\n        __typename\n      }\n      tocLink {\n        translation\n        __typename\n      }\n      showAdditionalInfoIcon\n      __typename\n    }\n    isClosed\n    paymentConfig {\n      installments {\n        minPriceFormatted\n        maxAcceptCount\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  badges {\n    caption {\n      translation\n      __typename\n    }\n    closedFacilities {\n      startDate\n      endDate\n      __typename\n    }\n    __typename\n  }\n  customBadges {\n    showSkiToDoor\n    showBhTravelCreditBadge\n    showOnlineCheckinBadge\n    __typename\n  }\n  description {\n    text\n    __typename\n  }\n  displayName {\n    text\n    translationTag {\n      translation\n      __typename\n    }\n    __typename\n  }\n  geniusInfo {\n    benefitsCommunication {\n      header {\n        title\n        __typename\n      }\n      items {\n        title\n        __typename\n      }\n      __typename\n    }\n    geniusBenefits\n    geniusBenefitsData {\n      hotelCardHasFreeBreakfast\n      hotelCardHasFreeRoomUpgrade\n      sortedBenefits\n      __typename\n    }\n    showGeniusRateBadge\n    __typename\n  }\n  location {\n    displayLocation\n    mainDistance\n    mainDistanceDescription\n    publicTransportDistanceDescription\n    skiLiftDistance\n    beachDistance\n    nearbyBeachNames\n    beachWalkingTime\n    geoDistanceMeters\n    isCentrallyLocated\n    isWithinBestLocationScoreArea\n    popularFreeDistrictName\n    nearbyUsNaturalParkText\n    __typename\n  }\n  mealPlanIncluded {\n    mealPlanType\n    text\n    __typename\n  }\n  persuasion {\n    autoextended\n    geniusRateAvailable\n    highlighted\n    preferred\n    preferredPlus\n    showNativeAdLabel\n    nativeAdId\n    nativeAdsCpc\n    nativeAdsTracking\n    sponsoredAdsData {\n      isDsaCompliant\n      legalEntityName\n      designType\n      __typename\n    }\n    __typename\n  }\n  policies {\n    showFreeCancellation\n    showNoPrepayment\n    showPetsAllowedForFree\n    enableJapaneseUsersSpecialCase\n    __typename\n  }\n  ribbon {\n    ribbonType\n    text\n    __typename\n  }\n  recommendedDate {\n    checkin\n    checkout\n    lengthOfStay\n    __typename\n  }\n  showGeniusLoginMessage\n  hostTraderLabel\n  soldOutInfo {\n    isSoldOut\n    messages {\n      text\n      __typename\n    }\n    alternativeDatesMessages {\n      text\n      __typename\n    }\n    __typename\n  }\n  nbWishlists\n  nonMatchingFlexibleFilterOptions {\n    label\n    __typename\n  }\n  visibilityBoosterEnabled\n  showAdLabel\n  isNewlyOpened\n  propertySustainability {\n    isSustainable\n    certifications {\n      name\n      __typename\n    }\n    __typename\n  }\n  seoThemes {\n    caption\n    __typename\n  }\n  relocationMode {\n    distanceToCityCenterKm\n    distanceToCityCenterMiles\n    distanceToOriginalHotelKm\n    distanceToOriginalHotelMiles\n    phoneNumber\n    __typename\n  }\n  bundleRatesAvailable\n  __typename\n}\n\nfragment Banner on Banner {\n  name\n  type\n  isDismissible\n  showAfterDismissedDuration\n  position\n  requestAlternativeDates\n  merchId\n  title {\n    text\n    __typename\n  }\n  imageUrl\n  paragraphs {\n    text\n    __typename\n  }\n  metadata {\n    key\n    value\n    __typename\n  }\n  pendingReviewInfo {\n    propertyPhoto {\n      lowResUrl {\n        relativeUrl\n        __typename\n      }\n      lowResJpegUrl {\n        relativeUrl\n        __typename\n      }\n      __typename\n    }\n    propertyName\n    urlAccessCode\n    __typename\n  }\n  nbDeals\n  primaryAction {\n    text {\n      text\n      __typename\n    }\n    action {\n      name\n      context {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  secondaryAction {\n    text {\n      text\n      __typename\n    }\n    action {\n      name\n      context {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  iconName\n  flexibleFilterOptions {\n    optionId\n    filterName\n    __typename\n  }\n  trackOnView {\n    type\n    experimentHash\n    value\n    __typename\n  }\n  dateFlexQueryOptions {\n    text {\n      text\n      __typename\n    }\n    action {\n      name\n      context {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    isApplied\n    __typename\n  }\n  __typename\n}\n\nfragment Carousel on Carousel {\n  aggregatedCountsByFilterId\n  carouselId\n  position\n  contentType\n  hotelId\n  name\n  soldoutProperties\n  priority\n  themeId\n  title {\n    text\n    __typename\n  }\n  slides {\n    captionText {\n      text\n      __typename\n    }\n    name\n    photoUrl\n    subtitle {\n      text\n      __typename\n    }\n    type\n    title {\n      text\n      __typename\n    }\n    action {\n      context {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationLocation on DestinationLocation {\n  name {\n    text\n    __typename\n  }\n  inName {\n    text\n    __typename\n  }\n  countryCode\n  ufi\n  __typename\n}\n\nfragment FilterData on Filter {\n  trackOnView {\n    type\n    experimentHash\n    value\n    __typename\n  }\n  trackOnClick {\n    type\n    experimentHash\n    value\n    __typename\n  }\n  name\n  field\n  category\n  filterStyle\n  title {\n    text\n    translationTag {\n      translation\n      __typename\n    }\n    __typename\n  }\n  subtitle\n  options {\n    parentId\n    genericId\n    trackOnView {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnClick {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnSelect {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnDeSelect {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnViewPopular {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnClickPopular {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnSelectPopular {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnDeSelectPopular {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    ...FilterOption\n    __typename\n  }\n  filterLayout {\n    isCollapsable\n    collapsedCount\n    __typename\n  }\n  stepperOptions {\n    min\n    max\n    default\n    selected\n    title {\n      text\n      translationTag {\n        translation\n        __typename\n      }\n      __typename\n    }\n    field\n    labels {\n      text\n      translationTag {\n        translation\n        __typename\n      }\n      __typename\n    }\n    trackOnView {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnClick {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnSelect {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnDeSelect {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnClickDecrease {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnClickIncrease {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnDecrease {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    trackOnIncrease {\n      type\n      experimentHash\n      value\n      __typename\n    }\n    __typename\n  }\n  sliderOptions {\n    min\n    max\n    minSelected\n    maxSelected\n    minPriceStep\n    minSelectedFormatted\n    currency\n    histogram\n    selectedRange {\n      translation\n      __typename\n    }\n    __typename\n  }\n  distanceToPoiData {\n    options {\n      text\n      value\n      isDefault\n      __typename\n    }\n    poiNotFound\n    poiPlaceholder\n    poiHelper\n    isSelected\n    selectedOptionValue\n    selectedPlaceId {\n      numValue\n      stringValue\n      __typename\n    }\n    selectedPoiType {\n      destType\n      source\n      __typename\n    }\n    selectedPoiText\n    selectedPoiLatitude\n    selectedPoiLongitude\n    __typename\n  }\n  __typename\n}\n\nfragment FilterOption on Option {\n  optionId: id\n  count\n  selected\n  urlId\n  source\n  field\n  additionalLabel {\n    text\n    translationTag {\n      translation\n      __typename\n    }\n    __typename\n  }\n  value {\n    text\n    translationTag {\n      translation\n      __typename\n    }\n    __typename\n  }\n  starRating {\n    value\n    symbol\n    caption {\n      translation\n      __typename\n    }\n    showAdditionalInfoIcon\n    __typename\n  }\n  __typename\n}\n\nfragment LandingPageBreadcrumb on LandingPageBreadcrumb {\n  destType\n  name\n  urlParts\n  __typename\n}\n\nfragment MatchingUnitConfigurations on SearchResultProperty {\n  matchingUnitConfigurations {\n    commonConfiguration {\n      name\n      unitId\n      bedConfigurations {\n        beds {\n          count\n          type\n          __typename\n        }\n        nbAllBeds\n        __typename\n      }\n      nbAllBeds\n      nbBathrooms\n      nbBedrooms\n      nbKitchens\n      nbLivingrooms\n      nbUnits\n      unitTypeNames {\n        translation\n        __typename\n      }\n      localizedArea {\n        localizedArea\n        unit\n        __typename\n      }\n      __typename\n    }\n    unitConfigurations {\n      name\n      unitId\n      bedConfigurations {\n        beds {\n          count\n          type\n          __typename\n        }\n        nbAllBeds\n        __typename\n      }\n      apartmentRooms {\n        config {\n          roomId: id\n          roomType\n          bedTypeId\n          bedCount: count\n          __typename\n        }\n        roomName: tag {\n          tag\n          translation\n          __typename\n        }\n        __typename\n      }\n      nbAllBeds\n      nbBathrooms\n      nbBedrooms\n      nbKitchens\n      nbLivingrooms\n      nbUnits\n      unitTypeNames {\n        translation\n        __typename\n      }\n      localizedArea {\n        localizedArea\n        unit\n        __typename\n      }\n      unitTypeId\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyBlocks on SearchResultProperty {\n  blocks {\n    blockId {\n      roomId\n      occupancy\n      policyGroupId\n      packageId\n      mealPlanId\n      bundleId\n      __typename\n    }\n    finalPrice {\n      amount\n      currency\n      __typename\n    }\n    originalPrice {\n      amount\n      currency\n      __typename\n    }\n    onlyXLeftMessage {\n      tag\n      variables {\n        key\n        value\n        __typename\n      }\n      translation\n      __typename\n    }\n    freeCancellationUntil\n    hasCrib\n    blockMatchTags {\n      childStaysForFree\n      freeStayChildrenAges\n      __typename\n    }\n    thirdPartyInventoryContext {\n      isTpiBlock\n      __typename\n    }\n    bundle @include(if: $includeBundle) {\n      highlightedText\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PriceDisplayInfoIrene on PriceDisplayInfoIrene {\n  badges {\n    name {\n      translation\n      __typename\n    }\n    tooltip {\n      translation\n      __typename\n    }\n    style\n    identifier\n    __typename\n  }\n  chargesInfo {\n    translation\n    __typename\n  }\n  displayPrice {\n    copy {\n      translation\n      __typename\n    }\n    amountPerStay {\n      amount\n      amountRounded\n      amountUnformatted\n      currency\n      __typename\n    }\n    amountPerStayHotelCurr {\n      amount\n      amountRounded\n      amountUnformatted\n      currency\n      __typename\n    }\n    __typename\n  }\n  averagePricePerNight {\n    amount\n    amountRounded\n    amountUnformatted\n    currency\n    __typename\n  }\n  priceBeforeDiscount {\n    copy {\n      translation\n      __typename\n    }\n    amountPerStay {\n      amount\n      amountRounded\n      amountUnformatted\n      currency\n      __typename\n    }\n    __typename\n  }\n  rewards {\n    rewardsList {\n      termsAndConditions\n      amountPerStay {\n        amount\n        amountRounded\n        amountUnformatted\n        currency\n        __typename\n      }\n      breakdown {\n        productType\n        amountPerStay {\n          amount\n          amountRounded\n          amountUnformatted\n          currency\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    rewardsAggregated {\n      amountPerStay {\n        amount\n        amountRounded\n        amountUnformatted\n        currency\n        __typename\n      }\n      copy {\n        translation\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  useRoundedAmount\n  discounts {\n    amount {\n      amount\n      amountRounded\n      amountUnformatted\n      currency\n      __typename\n    }\n    name {\n      translation\n      __typename\n    }\n    description {\n      translation\n      __typename\n    }\n    itemType\n    productId\n    __typename\n  }\n  excludedCharges {\n    excludeChargesAggregated {\n      copy {\n        translation\n        __typename\n      }\n      amountPerStay {\n        amount\n        amountRounded\n        amountUnformatted\n        currency\n        __typename\n      }\n      __typename\n    }\n    excludeChargesList {\n      chargeMode\n      chargeInclusion\n      chargeType\n      amountPerStay {\n        amount\n        amountRounded\n        amountUnformatted\n        currency\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  taxExceptions {\n    shortDescription {\n      translation\n      __typename\n    }\n    longDescription {\n      translation\n      __typename\n    }\n    __typename\n  }\n  displayConfig {\n    key\n    value\n    __typename\n  }\n  serverTranslations {\n    key\n    value\n    __typename\n  }\n  __typename\n}\n\nfragment BookerExperienceData on SearchResultProperty {\n  bookerExperienceContentUIComponentProps {\n    ... on BookerExperienceContentLoyaltyBadgeListProps {\n      badges {\n        amount\n        variant\n        key\n        title\n        hidePopover\n        popover\n        tncMessage\n        tncUrl\n        logoSrc\n        logoAlt\n        __typename\n      }\n      __typename\n    }\n    ... on BookerExperienceContentFinancialBadgeProps {\n      paymentMethod\n      backgroundColor\n      hideAccepted\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TopPhotos on SearchResultProperty {\n  topPhotos {\n    highResUrl {\n      relativeUrl\n      __typename\n    }\n    lowResUrl {\n      relativeUrl\n      __typename\n    }\n    highResJpegUrl {\n      relativeUrl\n      __typename\n    }\n    lowResJpegUrl {\n      relativeUrl\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SearchMetadata on SearchMeta {\n  availabilityInfo {\n    hasLowAvailability\n    unavailabilityPercent\n    totalAvailableNotAutoextended\n    totalAutoextendedAvailable\n    __typename\n  }\n  boundingBoxes {\n    swLat\n    swLon\n    neLat\n    neLon\n    type\n    __typename\n  }\n  childrenAges\n  dates {\n    checkin\n    checkout\n    lengthOfStayInDays\n    __typename\n  }\n  destId\n  destType\n  guessedLocation {\n    destId\n    destType\n    destName\n    __typename\n  }\n  maxLengthOfStayInDays\n  nbRooms\n  nbAdults\n  nbChildren\n  userHasSelectedFilters\n  customerValueStatus\n  isAffiliateBookingOwned\n  affiliatePartnerChannelId\n  affiliateVerticalType\n  geniusLevel\n  __typename\n}\n\nfragment SearchResultsBreadcrumb on SearchResultsBreadcrumb {\n  destId\n  destType\n  name\n  __typename\n}\n\nfragment SorterFields on SorterOption {\n  type: name\n  captionTranslationTag {\n    translation\n    __typename\n  }\n  tooltipTranslationTag {\n    translation\n    __typename\n  }\n  isSelected: selected\n  __typename\n}\n\nfragment TripTypesData on TripTypes {\n  beach {\n    isBeachUfi\n    isEnabledBeachUfi\n    __typename\n  }\n  ski {\n    isSkiExperience\n    isSkiScaleUfi\n    __typename\n  }\n  __typename\n}\n\nfragment ZeroResultsSection on ZeroResultsSection {\n  title {\n    text\n    __typename\n  }\n  primaryAction {\n    text {\n      text\n      __typename\n    }\n    action {\n      name\n      __typename\n    }\n    __typename\n  }\n  paragraphs {\n    text\n    __typename\n  }\n  type\n  __typename\n}\n\nfragment PreviousSearches on PreviousSearch {\n  childrenAges\n  __typename\n}\n\nfragment MerchRegionIrene on MerchComponentsResultIrene {\n  regions {\n    id\n    components {\n      ... on PromotionalBannerIrene {\n        promotionalBannerCampaignId\n        contentArea {\n          title {\n            ... on PromotionalBannerSimpleTitleIrene {\n              value\n              __typename\n            }\n            __typename\n          }\n          subTitle {\n            ... on PromotionalBannerSimpleSubTitleIrene {\n              value\n              __typename\n            }\n            __typename\n          }\n          caption {\n            ... on PromotionalBannerSimpleCaptionIrene {\n              value\n              __typename\n            }\n            ... on PromotionalBannerCountdownCaptionIrene {\n              campaignEnd\n              __typename\n            }\n            __typename\n          }\n          buttons {\n            variant\n            cta {\n              ariaLabel\n              text\n              targetLanding {\n                ... on OpenContextSheet {\n                  sheet {\n                    ... on WebContextSheet {\n                      title\n                      body {\n                        items {\n                          ... on ContextSheetTextItem {\n                            text\n                            __typename\n                          }\n                          ... on ContextSheetList {\n                            items {\n                              text\n                              __typename\n                            }\n                            __typename\n                          }\n                          __typename\n                        }\n                        __typename\n                      }\n                      buttons {\n                        variant\n                        cta {\n                          text\n                          ariaLabel\n                          targetLanding {\n                            ... on DirectLinkLanding {\n                              urlPath\n                              queryParams {\n                                name\n                                value\n                                __typename\n                              }\n                              __typename\n                            }\n                            ... on LoginLanding {\n                              stub\n                              __typename\n                            }\n                            ... on DeeplinkLanding {\n                              urlPath\n                              queryParams {\n                                name\n                                value\n                                __typename\n                              }\n                              __typename\n                            }\n                            ... on ResolvedLinkLanding {\n                              url\n                              __typename\n                            }\n                            __typename\n                          }\n                          __typename\n                        }\n                        __typename\n                      }\n                      __typename\n                    }\n                    __typename\n                  }\n                  __typename\n                }\n                ... on SearchResultsLandingIrene {\n                  destType\n                  destId\n                  checkin\n                  checkout\n                  nrAdults\n                  nrChildren\n                  childrenAges\n                  nrRooms\n                  filters {\n                    name\n                    value\n                    __typename\n                  }\n                  __typename\n                }\n                ... on DirectLinkLandingIrene {\n                  urlPath\n                  queryParams {\n                    name\n                    value\n                    __typename\n                  }\n                  __typename\n                }\n                ... on LoginLandingIrene {\n                  stub\n                  __typename\n                }\n                ... on DeeplinkLandingIrene {\n                  urlPath\n                  queryParams {\n                    name\n                    value\n                    __typename\n                  }\n                  __typename\n                }\n                ... on SorterLandingIrene {\n                  sorterName\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        designVariant {\n          ... on DesktopPromotionalFullBleedImageIrene {\n            image: image {\n              id\n              url(width: 814, height: 138)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on DesktopPromotionalImageLeftIrene {\n            imageOpt: image {\n              id\n              url(width: 248, height: 248)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on DesktopPromotionalImageRightIrene {\n            imageOpt: image {\n              id\n              url(width: 248, height: 248)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on MdotPromotionalFullBleedImageIrene {\n            image: image {\n              id\n              url(width: 358, height: 136)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on MdotPromotionalImageLeftIrene {\n            imageOpt: image {\n              id\n              url(width: 128, height: 128)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on MdotPromotionalImageRightIrene {\n            imageOpt: image {\n              id\n              url(width: 128, height: 128)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on MdotPromotionalIllustrationLeftIrene {\n            imageOpt: image {\n              id\n              url(width: 200, height: 200)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on MdotPromotionalIllustrationRightIrene {\n            imageOpt: image {\n              id\n              url(width: 200, height: 200)\n              alt\n              overlayGradient\n              primaryColorHex\n              __typename\n            }\n            colorScheme\n            signature\n            __typename\n          }\n          ... on MdotPromotionalImageTopIrene {\n            colorScheme\n            signature\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on MerchCarouselIrene @include(if: $carouselLowCodeExp) {\n        carouselCampaignId\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment VisualFiltersGroup on VisualFiltersGroup {\n  groupId: id\n  position\n  title {\n    text\n    __typename\n  }\n  visualFilters {\n    title {\n      text\n      __typename\n    }\n    description {\n      text\n      __typename\n    }\n    photoUrl\n    action {\n      name\n      context {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUspBadges on SearchResultProperty {\n  propertyUspBadges {\n    name\n    translatedName\n    __typename\n  }\n  __typename\n}\n"

            })

            headers = {
                'accept': '*/*',
                'accept-language': 'en-GB,en;q=0.9,ar-EG;q=0.8,ar;q=0.7,en-US;q=0.6',
                'apollographql-client-name': 'b-search-web-searchresults_rust',
                'apollographql-client-version': 'EQdHYKHU',
                'content-type': 'application/json',
                'origin': 'https://www.booking.com',
                'priority': 'u=1, i',
                'referer': 'https://www.booking.com/searchresults.ar.html',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'x-booking-context-action-name': 'searchresults_irene',
                'x-booking-context-aid': '304142',
                'x-booking-csrf-token': 'eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJjb250ZXh0LWVucmljaG1lbnQtYXBpIiwic3ViIjoiY3NyZi10b2tlbiIsImlhdCI6MTc1MjA3MTY2NiwiZXhwIjoxNzUyMTU4MDY2fQ.zfHK5SDu4Olq599lUFfUhjGBB7L2tUlk1jCr8nDb_FAj1UFHy9LHzaQGqFgI1hlPtVwwR8sMJPX2ewsXTQfF7w',
                'x-booking-dml-cluster': 'rust',
                'x-booking-et-serialized-state': 'E0WlHVyTQ1Y_nlatUS6KjDM-qVQ0y1YzGrnKtF_EQnoj3nvI9jO0WYjmgxSHbZ0fa',
                'x-booking-pageview-id': '09d7d10a227948219463cd7fc6a518e1',
                'x-booking-site-type-id': '1',
                'x-booking-topic': 'capla_browser_b-search-web-searchresults'
            }

            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            # Check if job should be stopped after network request
            if self.current_job_id and self._should_stop_job(self.current_job_id):
                self._log_message(f"Job {self.current_job_id} was stopped by user, returning empty results", "INFO")
                return [], 0
            
            result = response.json()
            results = result.get("data", {}).get("searchQueries", {}).get("search", {}).get("results", [])
            nb_results_total = result.get("data", {}).get("searchQueries", {}).get("search", {}).get("pagination", {}).get("nbResultsTotal", 0)
            
            page_links = [f"https://www.booking.com/hotel/sa/{property_info.get('basicPropertyData').get('pageName')}.ar.html"
                         for property_info in results if property_info.get('basicPropertyData', {}).get('pageName')]
            
            return page_links, nb_results_total
            
        except Exception as e:
            self._log_message(f"Error scraping hotels for city {city_name}: {str(e)}", "ERROR")
            return [], 0
    
    def scrape_city_complete(self, city_name: str, dest_id: int, sorter:str,city_or_country:str, csv_writer) -> int:
        """Scrape all hotels for a city with pagination"""
        offset = 0
        rows_per_page = 100
        counter = 0
        
        self._log_message(f"Starting to scrape city: {city_name} with destination ID: {dest_id}")
        
        while True:
            try:
                # Check if job should be stopped before each page
                if self.current_job_id and self._should_stop_job(self.current_job_id):
                    self._log_message(f"Job {self.current_job_id} was stopped by user, exiting city scraping", "INFO")
                    break
                
                counter += 1
                self._log_message(f"Processing page {counter} for city {city_name}, offset: {offset}")
                
                # Get hotel links for this page
                
                page_links, nb_results_total = self.scrape_city_hotels(city_name, dest_id,sorter,city_or_country, offset, rows_per_page)
                
                if not page_links:
                    self._log_message(f"No more results for city {city_name}, stopping")
                    break
                
                # Log progress
                self._log_message(f"Found {len(page_links)} links on page {counter} for city {city_name}")
                
                # Write new links to CSV
                new_links_count = 0
                for link in page_links:
                    if link not in self.scrapped_links:
                        csv_writer.writerow([counter, link, city_name])
                        self.scrapped_links.add(link)
                        new_links_count += 1
                
                self._log_message(f"Added {new_links_count} new links from page {counter} for city {city_name}")
                
                # Check if we should continue - use pagination info from response
                if offset > nb_results_total:
                    self._log_message(f"Reached end of results for city {city_name} (offset: {offset} > total: {nb_results_total})")
                    break
                
                # Also check if no more results (empty page)
                if len(page_links) == 0:
                    self._log_message(f"No more results for city {city_name} (empty page)")
                    break
                
                # Safety check to prevent infinite loops
                if counter > 50:  # Max 50 pages per city
                    self._log_message(f"Maximum page limit reached for city {city_name}")
                    break
                
                offset += rows_per_page
                
                # Add delay to avoid being blocked
                time.sleep(2)
                
            except Exception as e:
                self._log_message(f"Error processing page {counter} for city {city_name}: {str(e)}", "ERROR")
                break
        
        city_links = [link for link in self.scrapped_links if f"/{city_name.replace(' ', '').replace('-', '').lower()}" in link.lower()]
        return len(city_links)
    
    def run_link_scraping_job(self, job_id: int) -> Dict[str, Any]:

        
        """Run complete link scraping job for all cities"""
        self.current_job_id = job_id
        self.scrapped_links = set()
        
        try:
            # Read cities from file
            cities = []
            cities_file = "services/cities.txt"
            try:
                with open(cities_file, "r", encoding="utf-8") as f:
                    cities = [line.strip() for line in f.readlines() if len(line.strip()) > 2]
            except FileNotFoundError:
                self._log_message(f"cities.txt file not found at {cities_file}", "ERROR")
                self._update_job_progress(job_id, 0, "FAILED")
                return {"status": "FAILED", "error": f"cities.txt file not found at {cities_file}"}
            
            if not cities:
                self._log_message("No cities found in cities.txt", "ERROR")
                self._update_job_progress(job_id, 0, "FAILED")
                return {"status": "FAILED", "error": "No cities found"}
            
            self._log_message(f"Starting link scraping job {job_id} with {len(cities)} cities")
            self._update_job_progress(job_id, 0, "RUNNING")
            
            # Create CSV file with constant name
            csv_filename = "data/csv/booking_links.csv"
            csv_headers = ["counter", "page_link", "city"]
            
            # Ensure data directory exists
            import os
            os.makedirs("data/csv", exist_ok=True)
            
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(csv_headers)
                
                processed_cities = 0
                successful_cities = 0
                
                for city in cities:
                    # Check if job should be stopped
                    if self._should_stop_job(job_id):
                        self._log_message(f"Job {job_id} was stopped by user, exiting", "INFO")
                        return {"status": "STOPPED", "message": "Job stopped by user"}
                    
                    if "المملكة العربية السعودية" in city:
                        city_or_country="COUNTRY"
                    else:
                        city_or_country="CITY"
                    for sorter in Sorterings:
                        # Check if job should be stopped before each sorter
                        if self._should_stop_job(job_id):
                            self._log_message(f"Job {job_id} was stopped by user, exiting", "INFO")
                            return {"status": "STOPPED", "message": "Job stopped by user"}
                        
                        try:
                            self._log_message(f"Processing city: {city} with sorter: {sorter}")
                            
                            # Get destination ID
                            dest_id = self.get_city_destination_id(city)
                            if not dest_id:
                                self._log_message(f"Could not get destination ID for city: {city}", "WARN")
                                continue
                            
                            # Scrape all hotels for this city
                            city_links_count = self.scrape_city_complete(city, dest_id,sorter,city_or_country,writer)
                            
                            # Force flush to ensure data is written
                            csvfile.flush()
                            
                            self._log_message(f"Completed scraping for city {city}, found {city_links_count} unique links")
                            successful_cities += 1
                            
                            # Update progress
                            processed_cities += 1
                            self._update_job_progress(job_id, processed_cities)
                            
                            # Add delay between cities
                            time.sleep(3)
                            
                        except Exception as e:
                            self._log_message(f"Error processing city {city}: {str(e)}", "ERROR")
                            processed_cities += 1
                            self._update_job_progress(job_id, processed_cities)
                            continue
            
            # Complete the job
            total_links = len(self.scrapped_links)
            self._log_message(f"Link scraping job completed! Processed {processed_cities} cities, "
                            f"successful: {successful_cities}, total links: {total_links}")
            
            self._update_job_progress(job_id, processed_cities, "COMPLETED")
            
            return {
                "status": "COMPLETED",
                "processed_cities": processed_cities,
                "successful_cities": successful_cities,
                "total_links": total_links,
                "csv_filename": csv_filename
            }
            
        except Exception as e:
            self._log_message(f"Link scraping job failed: {str(e)}", "ERROR")
            self._update_job_progress(job_id, 0, "FAILED")
            return {"status": "FAILED", "error": str(e)} 