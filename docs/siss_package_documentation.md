# SSIS ETL Package Documentation

## Overview

This SSIS package handles the extraction, transformation, and loading (ETL) of attendance data from external sources into the SQL Server database.

## Package Details

### Source
- **Type**: CSV/Excel files or OLE DB source
- **Location**: `\\network\share\attendance\`
- **Format**: CSV with headers
- **Columns**:
  - Student_ID
  - Course_ID
  - Date
  - Status (Present/Absent/Late)

### Transformations

#### 1. Data Cleaning
- Remove null values
- Standardize date format (YYYY-MM-DD)
- Validate Student_ID and Course_ID against master tables

#### 2. Data Type Conversion
- Student_ID: INT
- Course_ID: INT
- Date: DATE
- Status: VARCHAR(10)

#### 3. Lookup Transformations
- Validate Student_ID exists in Student table
- Validate Course_ID exists in Course table
- Reject invalid records to error log

### Destination
- **Database**: ITI_Examination_System
- **Table**: Attendance
- **Load Type**: Full truncate and load (or incremental if needed)

## Execution

### Manual Execution

### Scheduled Execution
- **Frequency**: Daily at 2:00 AM
- **Error Handling**: Email notification on failure
- **Logging**: All errors logged to `ETL_Log` table

## Data Mappings

| Source Column | Destination Column | Transformation |
|---------------|-------------------|----------------|
| Student_ID | S_ID | Direct mapping |
| Course_ID | Course_ID | Direct mapping |
| Date | Date | Convert to DATE |
| Status | Status | Uppercase trim |

## Error Handling

- Invalid records redirected to `Attendance_Errors` table
- Email sent to admin on >5% error rate
- Daily summary report generated

## Performance
- **Average Runtime**: 5-10 minutes for 10,000 records
- **Indexing**: Indexes on S_ID, Course_ID, Date
- **Batch Size**: 1000 records per batch


