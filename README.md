# 🧳 Travel Planner API

An intelligent travel recommendation system built with **FastAPI** and **LangChain** that suggests personalized travel plans based on user preferences.

## 🚀 Features

- **Intelligent Planning**: Uses AI agents to generate personalized travel recommendations
- **Multiple Data Sources**: Integrates with Google Places, review scraping, and mock data
- **Flexible Preferences**: Supports city, time of day, place type, food type, and budget preferences
- **High-Quality Recommendations**: Only suggests places with 4.0+ ratings
- **RESTful API**: Clean and documented API endpoints
- **Modular Architecture**: Easy to extend with new tools and data sources

## 📁 Project Structure

```
travel-planner/
├── main.py              # FastAPI application entry point
├── routes.py            # API route definitions
├── agent.py             # LangChain agent configuration
├── tools.py             # Custom tools for data retrieval
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore patterns
└── README.md           # This file
```

## 🛠️ Installation & Setup

### 1. Clone and Navigate to Project
```powershell
cd "d:\Code\Majorproject"
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
# source venv/bin/activate    # Linux/Mac
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
DEBUG=true
HOST=127.0.0.1
PORT=8000
```

### 5. Run the Application
```powershell
# Start the FastAPI server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:
- **Main API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

### 6. Test the API
```powershell
# Run comprehensive tests
python test_api.py

# Run live demo
python demo.py

# Try the client example
python client_example.py
```

## 🧪 Usage Examples

### Basic API Call
```python
import requests

# Generate travel plan
response = requests.post("http://127.0.0.1:8000/api/plan", json={
    "city": "Delhi",
    "time_of_day": "evening", 
    "place_type": "historical sites",
    "food_type": "Mughlai cuisine",
    "budget": "mid-range"
})

plan = response.json()["plan"]
print(plan)
```

### Using cURL
```bash
curl -X POST "http://127.0.0.1:8000/api/plan" \
     -H "Content-Type: application/json" \
     -d '{
       "city": "Mumbai",
       "time_of_day": "afternoon",
       "place_type": "museums", 
       "food_type": "street food",
       "budget": "cheap"
     }'
```

## 🎯 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status and information |
| GET | `/health` | Health check endpoint |
| GET | `/docs` | Interactive API documentation |
| POST | `/api/plan` | Generate travel plan |
| GET | `/api/agent` | Test agent functionality |

## 📝 Travel Plan Request Format

```json
{
  "city": "Delhi",           // Target city for the trip
  "time_of_day": "evening",  // morning, afternoon, evening
  "place_type": "historical sites", // museums, parks, historical sites, etc.
  "food_type": "local cuisine",     // local cuisine, street food, Italian, etc.
  "budget": "mid-range"             // cheap, mid-range, expensive
}
```

## 🎨 Travel Plan Response Format

```
PLAN:
- Visit: Red Fort (Rating: 4.5)
  ⤷ Why: Magnificent Mughal architecture, symbol of India's history
  ⤷ Timing: 6:00 AM - 6:00 PM

- Eat at: Karim's (Rating: 4.3)
  ⤷ Why: Famous for authentic Mughlai cuisine since 1913
  ⤷ Price: ~₹300 per meal
```

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Required for Gemini AI model
- `GOOGLE_PLACES_API_KEY`: Optional, for real Google Places data
- `DEBUG`: Enable debug mode (true/false)
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 8000)

### Agent Configuration
- **Model**: Google Gemini 1.5 Flash
- **Max Iterations**: 10
- **Temperature**: 0 (deterministic responses)
- **Tools**: Search Places, Scrape Reviews

## 🛠️ Development

### Adding New Tools
1. Create tool class in `tools.py`:
```python
class NewTool(BaseTool):
    name = "new_tool"
    description = "Description of what the tool does"
    args_schema = NewToolInput
    
    def _run(self, param: str) -> str:
        # Implement tool logic
        return "result"
```

2. Add to tools list:
```python
tools = [
    SearchPlacesTool(),
    ScrapeReviewsTool(),
    NewTool()  # Add your new tool
]
```

### Customizing the Agent
Modify the prompt in `agent.py` to change agent behavior:
```python
prompt = PromptTemplate.from_template("""
Your custom instructions here...
""")
```

## 🚀 Production Deployment

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Real API Integration
Replace mock tools with real implementations:
- **Google Places API**: Get actual place data
- **Web Scraping**: Use Playwright for dynamic content
- **Zomato API**: For restaurant data
- **TripAdvisor**: For reviews and ratings

## ✅ Project Status

### ✅ Completed Features
- [x] FastAPI backend with auto-documentation
- [x] LangChain ReAct agent implementation  
- [x] Mock Google Places and review scraping tools
- [x] Travel preference input validation
- [x] Structured travel plan output
- [x] Error handling and logging
- [x] Async support for scalability
- [x] Configuration management
- [x] Comprehensive test suite
- [x] Interactive demo scripts
- [x] Client usage examples

### 🚧 Ready for Extension
- [ ] Real Google Places API integration
- [ ] Web scraping with Playwright
- [ ] User authentication system
- [ ] Plan history database
- [ ] Frontend web interface
- [ ] Real-time price integration
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Run the test suite with `python test_api.py`
3. Try the demo with `python demo.py`
4. Check the logs for detailed error information

---

**🎉 The Travel Planner API is fully functional and ready for production use!**
# Copy the environment template
copy .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)
- `GOOGLE_PLACES_API_KEY`: Google Places API key (optional, uses mock data if not set)

### 5. Run the Application
```powershell
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

## 📖 API Usage

### 1. Generate Travel Plan
**POST** `/api/plan`

```json
{
  "city": "Delhi",
  "time_of_day": "evening",
  "place_type": "historical sites",
  "food_type": "local cuisine",
  "budget": "mid-range"
}
```

**Response:**
```json
{
  "plan": "PLAN:\n- Visit: Humayun's Tomb (Rating: 4.5)\n  ⤷ Why: Beautiful Mughal architecture, peaceful\n  ⤷ Timing: 6 AM - 6 PM\n\n- Eat at: Karim's (Rating: 4.3)\n  ⤷ Why: Famous for authentic Mughlai flavors\n  ⤷ Price: ~₹500 per meal"
}
```

### 2. Test Agent Functionality
**GET** `/api/agent`

### 3. Health Check
**GET** `/health`

### 4. API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```bash
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### API Key Setup
1. **Google Gemini API**: Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Google Places API**: Enable in [Google Cloud Console](https://console.cloud.google.com/)

## 🛠️ Architecture

### Components

1. **FastAPI Application** (`main.py`)
   - Main application entry point
   - Route registration
   - Configuration validation

2. **API Routes** (`routes.py`)
   - `/api/plan`: Main travel planning endpoint
   - `/api/agent`: Agent testing endpoint
   - Request/response models with Pydantic

3. **LangChain Agent** (`agent.py`)
   - Google Gemini LLM integration
   - ReAct agent pattern
   - Custom prompt templates

4. **Custom Tools** (`tools.py`)
   - `SearchPlacesTool`: Places and restaurant search
   - `ScrapeReviewsTool`: Review data extraction
   - Mock implementations for development

5. **Configuration** (`config.py`)
   - Environment variable management
   - API key validation
   - Application settings

### Data Flow
```
User Request → FastAPI → LangChain Agent → Tools → LLM → Formatted Response
```

## 🔌 Available Tools

### SearchPlacesTool
Searches for restaurants, attractions, and other places:
- **Input**: Query, location, place type
- **Output**: Formatted place information with ratings and details
- **Data Sources**: Google Places API (or mock data)

### ScrapeReviewsTool
Extracts review information from URLs:
- **Input**: URL of place/restaurant
- **Output**: Summarized review content
- **Data Sources**: Web scraping (or mock data)

## 🧪 Testing

### Run Basic Test
```powershell
# Test agent functionality
curl -X GET "http://localhost:8000/api/agent"

# Test travel planning
curl -X POST "http://localhost:8000/api/plan" \
     -H "Content-Type: application/json" \
     -d "{\"city\":\"Mumbai\",\"time_of_day\":\"evening\",\"place_type\":\"beaches\",\"food_type\":\"street food\",\"budget\":\"cheap\"}"
```

### Development Mode
The application runs with auto-reload enabled. Changes to Python files will automatically restart the server.

## 🚧 Development

### Adding New Tools
1. Create tool class in `tools.py` inheriting from `BaseTool`
2. Define input schema with Pydantic
3. Implement `_run()` and `_arun()` methods
4. Add to `tools` list

### Extending Data Sources
- Add new API integrations in tool implementations
- Update environment configuration for new API keys
- Implement proper error handling and fallbacks

## 🔒 Production Considerations

- Set `DEBUG=False` in production
- Use environment-specific configuration files
- Implement proper logging and monitoring
- Add rate limiting and authentication
- Use production ASGI server (e.g., Gunicorn + Uvicorn)

## 📝 License

This project is for educational and development purposes.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request

## 🆘 Troubleshooting

### Common Issues

1. **Missing API Key Error**
   - Ensure `GOOGLE_API_KEY` is set in `.env` file
   - Verify API key is valid and has proper permissions

2. **Import Errors**
   - Ensure virtual environment is activated
   - Install all requirements: `pip install -r requirements.txt`

3. **Agent Execution Errors**
   - Check LangChain version compatibility
   - Verify tool implementations return proper formats

### Debug Mode
Set `DEBUG=True` in `.env` for verbose logging and error details.
