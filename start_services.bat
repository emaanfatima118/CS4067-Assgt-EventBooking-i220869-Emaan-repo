@echo off
echo Starting all services...

REM Start User Service (FastAPI)
start cmd /k "cd /d C:\Users\hp\Desktop\Semester 6\devopsAss1\CS4067-Assgt-EventBooking-i220869-Emaan-repo\UserService && uvicorn main:app --host 127.0.0.1 --port 8002 --reload"

timeout /t 5

REM Start Event Service (FastAPI)
start cmd /k "cd /d C:\Users\hp\Desktop\Semester 6\devopsAss1\CS4067-Assgt-EventBooking-i220869-Emaan-repo\EventService && uvicorn event_service:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 5

REM Start Payment Service (Flask)
start cmd /k "cd /d C:\Users\hp\Desktop\Semester 6\devopsAss1\CS4067-Assgt-EventBooking-i220869-Emaan-repo\PaymentService && python payment_service.py"

timeout /t 5

REM Start Booking Service (FastAPI) - If you have one
start cmd /k "cd /d C:\Users\hp\Desktop\Semester 6\devopsAss1\CS4067-Assgt-EventBooking-i220869-Emaan-repo\BookingService && python booking_service.py"

timeout /t 5

REM Start Notification Service (RabbitMQ Consumer)
start cmd /k "cd /d C:\Users\hp\Desktop\Semester 6\devopsAss1\CS4067-Assgt-EventBooking-i220869-Emaan-repo\NotificationService && python notification_service.py"

echo All services started!
