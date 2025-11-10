
## Component Details

### 1. Web Application (Flask)
- **Framework**: Flask 3.0
- **Database Driver**: pyodbc
- **Session Management**: Flask sessions with secure cookies
- **Password Security**: bcrypt hashing

### 2. Database
- **DBMS**: Microsoft SQL Server
- **Connection**: pyodbc with connection pooling
- **Transactions**: ACID compliance
- **Backup**: Manual SQL backups

### 3. ETL Pipeline
- **Tool**: SQL Server Integration Services (SSIS)
- **Purpose**: Attendance data loading
- **Frequency**: Daily batch processing
- **Data Volume**: 10,000+ records

### 4. AI/ML Components
- **Chatbot**: Google Gemini 2.5 Flash API
- **ML Models**: scikit-learn (Linear Regression)
- **Use Cases**:
  - Student grade prediction
  - Pass/fail rate forecasting
  - Performance trend analysis

### 5. Security
- Password hashing with bcrypt
- Session-based authentication
- Role-based access control (RBAC)
- SQL injection prevention (parameterized queries)
- CSRF protection

## Data Flow

### Student Takes Exam
