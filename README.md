## Screenshots of the UI
<img width="1919" height="922" alt="Screenshot 2026-04-18 194116" src="https://github.com/user-attachments/assets/8d2bbd22-c740-4ffd-b814-4b3bf7777c1e" />
<img width="1919" height="919" alt="Screenshot 2026-04-18 194416" src="https://github.com/user-attachments/assets/273b7d9c-de33-4dbb-a108-154eed547556" />
<img width="1918" height="914" alt="Screenshot 2026-04-18 194905" src="https://github.com/user-attachments/assets/808fb64b-7788-4ace-a97b-982c3e24278b" />
<img width="1919" height="926" alt="Screenshot 2026-04-18 194923" src="https://github.com/user-attachments/assets/65d3caa5-2155-4011-9e18-cf7af959231e" />
<img width="1919" height="926" alt="Screenshot 2026-04-18 194959" src="https://github.com/user-attachments/assets/7a88fd8b-30c2-49e3-91ad-48ba7b199f7e" />
<img width="1919" height="916" alt="Screenshot 2026-04-18 195027" src="https://github.com/user-attachments/assets/fb065090-e25b-4eae-b95c-fa9079681f27" />


## Setup instructions for running the application

Step 1: Clone the Repository

Step 2: Environment Variables

  set up the environment variables for API keys and database configurations.

Step 3: Set Up the Django Backend

  Install Python dependencies
  
  Run Database Migrations
  
  Start the Django Development Server
  
Step 4: Set Up the Next.js Frontend

  Install Node dependencies
  
  Start the Next.js Development Server

## API documentation

Base URL: http://localhost:8000/api

### Book Management Endpoints

1. List All Books
   
  Retrieves a list of all processed books. Supports filtering and sorting.
  
  URL: /books/
  
  Method: GET
  
  Query Parameters (Optional):
  
  search (string): Search by book title.
  
  category (string): Filter by book category.
  
  genre (string): Filter by book genre.
  
  ordering (string): Sort the results. Valid options: title, -title, rating, -rating, created_at, -created_at.
  
  Success Response: 200 OK (Returns an array of book objects)
  
2. Get Book Details
   
  Retrieves full details, including AI-generated insights, for a specific book.
  
  URL: /books/{id}/
  
  Method: GET
  
  URL Parameters:
  
  id (integer): The unique ID of the book.
  
  Success Response: 200 OK (Returns a detailed book object)
  
  Error Response: 404 Not Found (If the book doesn't exist)
  
3. Get Book Recommendations
   
  Fetches up to 6 related book recommendations based on a specific book.
  
  URL: /books/{id}/recommendations/
  
  Method: GET
  
  URL Parameters:
  
  id (integer): The unique ID of the source book.
  
  Success Response: 200 OK (Returns an array of recommended book objects)
  
  Error Response: 404 Not Found (If the source book doesn't exist)
  
### Upload & Scraping Endpoints

4. Upload Book Manually
   
  Uploads a new book manually, triggers AI insight processing, and indexes the content for Question & Answering (RAG).
  
  URL: /books/upload/
  
  Method: POST
  
  Body Data (JSON): Requires fields defined in your BookUploadSerializer (e.g., title, author, description).
  
  Success Response: 201 Created (Returns the newly created book object)
  
  Error Response: 400 Bad Request (If validation fails)
  
5. Trigger Web Scraper
   
  Starts a background Selenium task to scrape books from the web, process their AI insights, and index them.
  
  URL: /books/scrape/
  
  Method: POST
  
  Body Data (JSON):
  
  max_books (integer, optional): Maximum number of books to scrape. Default is 30, max limit is 200.
  
  Success Response: 200 OK (Returns a status message indicating the scraper started)
  
  Error Response: 409 Conflict (If a scraping task is already running)
  
6. Check Scraper Status
   
  Retrieves the real-time progress of the currently running scraper task.
  
  URL: /books/scrape-status/
  
  Method: GET
  
  Success Response: 200 OK
  
  Response Format:
  
  {
    "is_running": true,
    "progress": 15,
    "total": 30,
    "current_book": "The Great Gatsby",
    "error": null
  }

### AI & RAG Endpoints

  Allows users to ask intelligent questions about the books in the database. The AI fetches the most relevant book chunks and provides an answer.
  
  URL: /books/ask/
  
  Method: POST
  
  Body Data (JSON):
  
  question (string, required): The question to ask.
  
  top_k (integer, optional): Number of relevant book chunks to use for context. Defaults to 5.
  
  Success Response: 200 OK
  
  Response Format:
  {
    "answer": "The AI-generated response...",
    "sources": [
      {"book_id": 1, "title": "...", "content_snippet": "..."}
    ]
  }
  Error Response: 400 Bad Request (If the question is missing or invalid)

  ## Sample questions and answers from my system
  
  Example 1: This is the beginning of a new journey
  Response: Based on the retrieved context:

[Source: Sapiens: A Brief History of Humankind]
We are acquiring the ability to design not only the world around us, but also ourselves. Where is this leading us, and what do we want to become?Featuring 27 photographs, 6 maps, and 25 illustrations/diagrams, this provocative and insightful work is sure to spark debate and is essential reading for aficionados of Jared Diamond, James Gleick, Matt Ridley, Robert Wright, and Sharon Moalem. ...more Summary: From a renowned historian comes a groundbrea...

[Sources: Sapiens: A Brief History of Humankind, In Her Wake, The Black Maria, The Dirty Little Secrets of Getting Your Dream Job, How Music Works]

  Example 2: Why does Jay Gatsby throw such extravagant parties in 'The Great Gatsby'?
  Response: Based on the retrieved context:

[Source: Set Me Free]
Title: Set Me Free.
Category: Young Adult.
Description: Aaron Ledbetter’s future had been planned out for him since before he was born. Each year, the Ledbetter family vacation on Tybee Island gave Aaron a chance to briefly free himself from his family’s expectations. When he meets Jonas “Lucky” Luckett, a caricature artist in town with the traveling carnival, he must choose between the life that’s been mapped out for him, and Aaron Ledbetter’s future had been planned out f...

[Sources: Set Me Free, Aladdin and His Wonderful Lamp, Scott Pilgrim's Precious Little Life (Scott Pilgrim #1), Black Dust, How Music Works]

