#!/usr/bin/env python3
"""
CSV to JSON Converter - Converts hotel CSV data to JSON format
Matches the structure of booking_hotels_data.json
"""

import pandas as pd
import json
import ast
import logging
from typing import Dict, List, Optional, Any
import argparse
import os
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVToJSONConverter:
    def __init__(self):
        """Initialize the converter."""
        pass
    
    def safe_json_loads(self, json_string: str) -> Any:
        """Safely parse JSON string, handling different formats."""
        if pd.isna(json_string) or json_string == '' or json_string is None or json_string == 'nan':
            return None
            
        # Convert to string if not already
        json_string = str(json_string).strip()
        
        # Handle empty or null-like strings
        if json_string in ['', '{}', '[]', 'null', 'None', 'nan']:
            return {} if json_string == '{}' else ([] if json_string == '[]' else None)
            
        try:
            # Try direct JSON parsing first
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            try:
                # Try using ast.literal_eval for Python-like strings
                return ast.literal_eval(json_string)
            except (ValueError, SyntaxError):
                try:
                    # Handle cases where outer quotes might be missing
                    if not json_string.startswith(('{', '[', '"')):
                        return None
                    
                    # Try with eval as last resort (be careful with this in production)
                    # Only for trusted data sources
                    if json_string.startswith(('{', '[')):
                        return eval(json_string)
                except:
                    pass
                
                logger.warning(f"Could not parse JSON: {json_string[:100]}...")
                return None
    
    def safe_get_value(self, row: Dict, key: str, default=None):
        """Safely get value from row dictionary, handling NaN and empty values."""
        value = row.get(key, default)
        if pd.isna(value) or value == '' or value == 'nan' or str(value).strip() == '':
            return None
        return str(value).strip() if value is not None else None
    
    def safe_get_numeric(self, row: Dict, key: str, is_float: bool = True):
        """Safely get numeric value from row dictionary."""
        value = self.safe_get_value(row, key)
        if value is None:
            return None
        
        try:
            if is_float:
                return float(value)
            else:
                return int(float(value))  # Convert to float first to handle strings like "5.0"
        except (ValueError, TypeError):
            return None
    
    def process_facilities(self, facilities_data: Dict) -> Dict:
        """Process facilities data to match the expected JSON format."""
        if not facilities_data or not isinstance(facilities_data, dict):
            return {}
        
        processed = {}
        for category, facility_info in facilities_data.items():
            if isinstance(facility_info, dict):
                # Extract SVG and sub_facilities
                svg = facility_info.get('svg', '')
                sub_facilities = facility_info.get('sub_facilities', {})
                
                # Handle null or empty SVG
                if not svg or svg == 'null':
                    svg = '<svg viewbox="0 0 128 128" width="50px" xmlns="http://www.w3.org/2000/svg"><path d="M56.33 100a4 4 0 0 1-2.82-1.16L20.68 66.12a4 4 0 1 1 5.64-5.65l29.57 29.46 45.42-60.33a4 4 0 1 1 6.38 4.8l-48.17 64a4 4 0 0 1-2.91 1.6z"></path></svg>'
                
                # Process sub_facilities
                processed_sub = {}
                if isinstance(sub_facilities, dict):
                    for sub_name, sub_icon in sub_facilities.items():
                        if not sub_icon or sub_icon == 'null':
                            sub_icon = '<svg viewbox="0 0 128 128" width="50px" xmlns="http://www.w3.org/2000/svg"><path d="M56.33 100a4 4 0 0 1-2.82-1.16L20.68 66.12a4 4 0 1 1 5.64-5.65l29.57 29.46 45.42-60.33a4 4 0 1 1 6.38 4.8l-48.17 64a4 4 0 0 1-2.91 1.6z"></path></svg>'
                        processed_sub[sub_name] = sub_icon
                
                processed[category] = {
                    "svg": svg,
                    "sub_facilities": processed_sub
                }
            else:
                # Handle facilities with null data
                processed[category] = {
                    "svg": '<svg viewbox="0 0 128 128" width="50px" xmlns="http://www.w3.org/2000/svg"><path d="M56.33 100a4 4 0 0 1-2.82-1.16L20.68 66.12a4 4 0 1 1 5.64-5.65l29.57 29.46 45.42-60.33a4 4 0 1 1 6.38 4.8l-48.17 64a4 4 0 0 1-2.91 1.6z"></path></svg>',
                    "sub_facilities": {}
                }
        
        return processed
    
    def process_most_famous_facilities(self, facilities_data: Dict) -> Dict:
        """Process most famous facilities data."""
        if not facilities_data or not isinstance(facilities_data, dict):
            return {}
        
        processed = {}
        for facility_name, icon in facilities_data.items():
            if not icon or icon == 'null':
                icon = '<svg viewbox="0 0 24 24" width="50px" xmlns="http://www.w3.org/2000/svg"><path d="M22.5 12c0 5.799-4.701 10.5-10.5 10.5S1.5 17.799 1.5 12 6.201 1.5 12 1.5 22.5 6.201 22.5 12m1.5 0c0-6.627-5.373-12-12-12S0 5.373 0 12s5.373 12 12 12 12-5.373 12-12m-9.75-1.5a1.5 1.5 0 0 1-1.5 1.5H10.5l.75.75v-4.5L10.5 9h2.25a1.5 1.5 0 0 1 1.5 1.5m1.5 0a3 3 0 0 0-3-3H10.5a.75.75 0 0 0-.75.75v4.5c0 .414.336.75.75.75h2.25a3 3 0 0 0 3-3m-4.5 6.75v-4.5a.75.75 0 0 0-1.5 0v4.5a.75.75 0 0 0 1.5 0"></path></svg>'
            processed[facility_name] = icon
        
        return processed
    
    def convert_row_to_json(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single CSV row to JSON format."""
        try:
            # Parse JSON fields
            image_links = self.safe_json_loads(self.safe_get_value(row, 'image_links', '[]'))
            most_famous_facilities = self.safe_json_loads(self.safe_get_value(row, 'most_famous_facilities', '{}'))
            all_facilities = self.safe_json_loads(self.safe_get_value(row, 'all_facilities', '{}'))
            
            # Build the hotel JSON object in the exact format of booking_hotels_data.json
            hotel_json = {
                "title": self.safe_get_value(row, 'title'),
                "address": self.safe_get_value(row, 'address'),
                "region": self.safe_get_value(row, 'region'),
                "postalCode": self.safe_get_value(row, 'postalCode'),
                "addressCountry": self.safe_get_value(row, 'addressCountry'),
                "latitude": str(self.safe_get_numeric(row, 'latitude')) if self.safe_get_numeric(row, 'latitude') is not None else None,
                "longitude": str(self.safe_get_numeric(row, 'longitude')) if self.safe_get_numeric(row, 'longitude') is not None else None,
                "description": self.safe_get_value(row, 'description'),
                "stars": self.safe_get_numeric(row, 'stars', is_float=False),
                "image_links": image_links if isinstance(image_links, list) else [],
                "most_famous_facilities": self.process_most_famous_facilities(most_famous_facilities),
                "all_facilities": self.process_facilities(all_facilities)
            }
            
            # Add optional fields only if they exist and are not empty
            rating_value = self.safe_get_numeric(row, 'rating_value')
            if rating_value is not None:
                hotel_json["rating_value"] = rating_value
            
            rating_text = self.safe_get_value(row, 'rating_text')
            if rating_text:
                hotel_json["rating_text"] = rating_text
            
            url = self.safe_get_value(row, 'url')
            if url:
                hotel_json["url"] = url
            
            # Remove None values to keep JSON clean
            cleaned_json = {k: v for k, v in hotel_json.items() if v is not None}
            
            return cleaned_json
            
        except Exception as e:
            logger.error(f"Error converting row to JSON: {e}")
            return None
    
    def read_csv_with_custom_parser(self, csv_file_path: str) -> List[Dict]:
        """Read CSV with custom parsing to handle complex multi-line data."""
        rows = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Read the raw content and handle complex multi-line fields
            content = file.read()
            
            # Use csv.reader with proper settings for complex data
            lines = content.split('\n')
            csv_reader = csv.reader(lines, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            
            headers = None
            current_row = []
            in_multiline = False
            
            for line_data in csv_reader:
                if headers is None:
                    headers = line_data
                    continue
                
                # Handle multi-line rows
                if len(line_data) == len(headers):
                    # Complete row
                    if current_row:
                        # Finish previous multi-line row
                        row_dict = dict(zip(headers, current_row))
                        rows.append(row_dict)
                        current_row = []
                    
                    if line_data and any(field.strip() for field in line_data):
                        current_row = line_data
                elif current_row:
                    # Continuation of multi-line field
                    if line_data:
                        # Append to the last field of current row
                        if current_row:
                            current_row[-1] += '\n' + ','.join(line_data)
            
            # Don't forget the last row
            if current_row and len(current_row) == len(headers):
                row_dict = dict(zip(headers, current_row))
                rows.append(row_dict)
        
        return rows
    
    def convert_csv_to_json(self, csv_file_path: str, output_file_path: str = None) -> bool:
        """Convert entire CSV file to JSON format."""
        try:
            logger.info(f"Reading CSV file: {csv_file_path}")
            
            # Try pandas first, then fall back to custom parser
            df = None
            rows = []
            
            try:
                # Try pandas with various approaches
                parsing_attempts = [
                    {
                        'encoding': 'utf-8',
                        'quotechar': '"',
                        'escapechar': None,
                        'na_values': ['', 'nan', 'null', 'None'],
                        'keep_default_na': False,
                        'skipinitialspace': True,
                        'engine': 'python'
                    }
                ]
                
                for i, params in enumerate(parsing_attempts):
                    try:
                        logger.info(f"Attempting pandas parsing method {i + 1}...")
                        df = pd.read_csv(csv_file_path, **params)
                        logger.info(f"Successfully parsed CSV with pandas method {i + 1}")
                        # Convert DataFrame to list of dictionaries
                        rows = df.to_dict('records')
                        break
                    except Exception as e:
                        logger.warning(f"Pandas parsing method {i + 1} failed: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Pandas parsing failed entirely: {e}")
            
            # If pandas failed, try custom parser
            if not rows:
                logger.info("Attempting custom CSV parsing...")
                try:
                    rows = self.read_csv_with_custom_parser(csv_file_path)
                    logger.info(f"Successfully parsed CSV with custom parser")
                except Exception as e:
                    logger.error(f"Custom parsing also failed: {e}")
                    return False
            
            if not rows:
                logger.error("All parsing methods failed")
                return False
                
            logger.info(f"Found {len(rows)} hotels in CSV file")
            
            # Convert each row to JSON
            hotels_json = []
            success_count = 0
            error_count = 0
            
            for i, row in enumerate(rows):
                try:
                    logger.info(f"Processing hotel {i + 1}/{len(rows)}")
                    
                    hotel_json = self.convert_row_to_json(row)
                    if hotel_json:
                        hotels_json.append(hotel_json)
                        success_count += 1
                    else:
                        error_count += 1
                        logger.warning(f"Skipped row {i + 1} due to conversion errors")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {i + 1}: {e}")
                    continue
            
            # Determine output file path
            if not output_file_path:
                base_name = os.path.splitext(csv_file_path)[0]
                output_file_path = f"{base_name}_converted.json"
            
            # Write JSON file
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(hotels_json, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Conversion completed. Success: {success_count}, Errors: {error_count}")
            logger.info(f"JSON file saved to: {output_file_path}")
            
            return error_count == 0
            
        except Exception as e:
            logger.error(f"Error converting CSV to JSON: {e}")
            return False


def main():
    """Main function to run CSV to JSON conversion."""
    parser = argparse.ArgumentParser(description='Convert hotel CSV data to JSON format')
    parser.add_argument('input_csv', help='Path to input CSV file')
    parser.add_argument('-o', '--output', help='Path to output JSON file (optional)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_csv):
        logger.error(f"Input file not found: {args.input_csv}")
        return False
    
    # Initialize converter
    converter = CSVToJSONConverter()
    
    # Convert CSV to JSON
    success = converter.convert_csv_to_json(args.input_csv, args.output)
    
    if success:
        print("✅ CSV to JSON conversion completed successfully!")
        return True
    else:
        print("❌ CSV to JSON conversion completed with errors. Check logs for details.")
        return False


if __name__ == "__main__":
    main() 