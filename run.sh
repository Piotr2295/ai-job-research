#!/bin/bash

# Start both backend and frontend servers
echo "Starting AI Job Research Agent..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill 0
}
trap cleanup EXIT

# Start backend in background
echo "Starting backend server..."
export KMP_DUPLICATE_LIB_OK=TRUE
source .venv/bin/activate && uvicorn app.main:app --reload &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "Starting frontend server..."
cd frontend && npm start &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID