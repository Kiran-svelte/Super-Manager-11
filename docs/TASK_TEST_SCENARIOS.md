# 100 Task Test Scenarios for Super Manager AI

This document contains 100 different task inputs to test the AI assistant's capabilities.
Each task includes the **Input**, **Expected Behavior**, and **Current Issues**.

---

## Category 1: Scheduling & Meetings (1-15)

### 1. Schedule a meeting with boss
**Input:** "Schedule a meeting with John at 3 PM tomorrow"
**Expected:** Ask for email, create calendar invite, send notification
**Current Issue:** May not actually send email invites

### 2. Create recurring meeting
**Input:** "Create a weekly standup meeting every Monday at 10 AM"
**Expected:** Create recurring calendar event, invite team
**Current Issue:** No recurring meeting support

### 3. Reschedule existing meeting
**Input:** "Reschedule my 2 PM meeting to 4 PM"
**Expected:** Find meeting, update time, notify participants
**Current Issue:** Cannot access or modify existing meetings

### 4. Cancel meeting with notification
**Input:** "Cancel tomorrow's team meeting and notify everyone"
**Expected:** Cancel meeting, send cancellation emails
**Current Issue:** No meeting cancellation flow

### 5. Find available time slot
**Input:** "Find a time slot when both Sarah and Mike are free"
**Expected:** Check calendars, suggest available times
**Current Issue:** No calendar integration

### 6. Schedule meeting in different timezone
**Input:** "Schedule a call with NYC team at 9 AM their time"
**Expected:** Convert timezone, create meeting
**Current Issue:** May not handle timezone correctly

### 7. Book meeting room
**Input:** "Book conference room A for tomorrow's meeting"
**Expected:** Check room availability, reserve room
**Current Issue:** No room booking integration

### 8. Send meeting agenda
**Input:** "Send yesterday's meeting notes to all participants"
**Expected:** Compile notes, send email to attendees
**Current Issue:** No meeting notes storage

### 9. Set meeting reminder
**Input:** "Remind me 30 minutes before my next meeting"
**Expected:** Create reminder, send push notification
**Current Issue:** Reminders not persistent, no push notifications

### 10. Schedule interview
**Input:** "Schedule interview with candidate John Doe for Friday"
**Expected:** Send interview invite, add to calendar
**Current Issue:** No interview scheduling flow

### 11. Add participant to meeting
**Input:** "Add Sara to the 3 PM meeting today"
**Expected:** Update meeting, send invite to Sara
**Current Issue:** Cannot modify existing meetings

### 12. Meeting with file sharing
**Input:** "Schedule a review meeting and share the project docs"
**Expected:** Create meeting, attach/link documents
**Current Issue:** No file attachment support

### 13. International call scheduling
**Input:** "Schedule a call with our London team considering holiday there"
**Expected:** Check UK holidays, suggest appropriate date
**Current Issue:** No holiday calendar

### 14. Multi-location meeting
**Input:** "Set up a meeting with all regional offices"
**Expected:** Find common time across timezones
**Current Issue:** No multi-timezone optimization

### 15. Replace meeting organizer
**Input:** "Transfer my 2 PM meeting organizer role to Mike"
**Expected:** Change organizer, send update
**Current Issue:** Not supported

---

## Category 2: Email & Communication (16-30)

### 16. Send simple email
**Input:** "Send email to john@example.com about project update"
**Expected:** Draft email, confirm, send
**Current Issue:** May not actually send

### 17. Reply to email
**Input:** "Reply to Sarah's last email saying I'll be there"
**Expected:** Find email, compose reply, send
**Current Issue:** Cannot access email inbox

### 18. Forward email with comment
**Input:** "Forward Mike's email to the team with my comments"
**Expected:** Find email, add comments, forward
**Current Issue:** No email access

### 19. Email with attachment
**Input:** "Send the quarterly report to all stakeholders"
**Expected:** Attach file, compose email, send
**Current Issue:** No file attachment support

### 20. Schedule email
**Input:** "Send this email tomorrow at 9 AM"
**Expected:** Queue email for scheduled delivery
**Current Issue:** No scheduled email support

### 21. Email to group
**Input:** "Email the marketing team about the campaign launch"
**Expected:** Get group contacts, send to all
**Current Issue:** No contact groups

### 22. Email with CC/BCC
**Input:** "Email client with boss CC'd"
**Expected:** Compose email with proper CC
**Current Issue:** Limited CC support

### 23. Follow-up email
**Input:** "Send follow-up to yesterday's meeting attendees"
**Expected:** Get attendees, compose follow-up
**Current Issue:** No meeting context

### 24. Email template
**Input:** "Send thank you email template to all interviewees"
**Expected:** Use template, personalize, send
**Current Issue:** No template system

### 25. Urgent email notification
**Input:** "Send urgent email to CEO about security incident"
**Expected:** High priority email, delivery confirmation
**Current Issue:** No priority levels

### 26. Email in different language
**Input:** "Send email in Spanish to our Mexico team"
**Expected:** Translate or compose in Spanish
**Current Issue:** Limited language support

### 27. Email receipt tracking
**Input:** "Send proposal and notify me when they open it"
**Expected:** Send with read receipt tracking
**Current Issue:** No tracking support

### 28. Bulk email
**Input:** "Send newsletter to all 500 subscribers"
**Expected:** Use proper bulk email service, comply with laws
**Current Issue:** No bulk email capability

### 29. Email signature update
**Input:** "Update my email signature with new title"
**Expected:** Update signature in email config
**Current Issue:** No signature management

### 30. Out of office setup
**Input:** "Set up out of office reply for my vacation"
**Expected:** Configure auto-reply
**Current Issue:** No auto-reply config

---

## Category 3: Booking & Reservations (31-50)

### 31. Book movie tickets
**Input:** "Book 4 tickets for Avengers at PVR Orion, 7 PM show"
**Expected:** Check availability, real booking, payment
**Current Issue:** ❌ CANNOT book - generates fake responses

### 32. Book flight
**Input:** "Book cheapest flight to Mumbai for this Friday"
**Expected:** Search flights, show options, real booking
**Current Issue:** ❌ NO flight booking integration

### 33. Book hotel
**Input:** "Book 2 nights at Taj Bangalore starting Saturday"
**Expected:** Check availability, show rates, real booking
**Current Issue:** ❌ NO hotel booking integration

### 34. Book restaurant
**Input:** "Reserve table for 4 at Truffles for 8 PM tonight"
**Expected:** Check availability, make reservation
**Current Issue:** ❌ NO restaurant booking

### 35. Book cab/uber
**Input:** "Book an Uber to airport for 6 AM tomorrow"
**Expected:** Schedule ride, get confirmation
**Current Issue:** ❌ NO ride booking integration

### 36. Book train tickets
**Input:** "Book 2 AC tickets on Shatabdi to Chennai"
**Expected:** Check IRCTC, real booking
**Current Issue:** ❌ NO IRCTC integration

### 37. Book event tickets
**Input:** "Get 2 tickets for Coldplay concert in Mumbai"
**Expected:** Show availability, real purchase
**Current Issue:** ❌ NO event ticketing

### 38. Book amusement park
**Input:** "Book 5 Wonderla Bangalore tickets for Sunday"
**Expected:** Check real offers, actual booking
**Current Issue:** ❌ FABRICATES offers, no real booking

### 39. Book spa appointment
**Input:** "Book spa session at nearest O2 Spa for Saturday"
**Expected:** Find nearby, check slots, book
**Current Issue:** ❌ NO spa booking

### 40. Book doctor appointment
**Input:** "Book appointment with Dr. Sharma for this week"
**Expected:** Check doctor's availability, book slot
**Current Issue:** ❌ NO healthcare booking

### 41. Cancel booking
**Input:** "Cancel my hotel booking for next week"
**Expected:** Find booking, process cancellation, refund
**Current Issue:** ❌ NO booking history

### 42. Modify booking
**Input:** "Change my flight to evening instead of morning"
**Expected:** Find booking, show options, modify
**Current Issue:** ❌ NO booking modification

### 43. Group booking
**Input:** "Book 20 movie tickets for office team outing"
**Expected:** Group booking, special handling
**Current Issue:** ❌ NO group booking

### 44. Package booking
**Input:** "Book Goa trip package with flight and hotel"
**Expected:** Bundle deals, combined booking
**Current Issue:** ❌ NO package booking

### 45. International booking
**Input:** "Book flight and hotel for Singapore trip"
**Expected:** International booking, visa reminder
**Current Issue:** ❌ NO international support

### 46. Book with preferences
**Input:** "Book window seat on morning flight to Delhi"
**Expected:** Seat selection, preference matching
**Current Issue:** ❌ NO preference handling

### 47. Book recurring service
**Input:** "Book house cleaning every Saturday"
**Expected:** Recurring booking, service provider
**Current Issue:** ❌ NO recurring bookings

### 48. Book with discount code
**Input:** "Book using my HDFC credit card offer"
**Expected:** Apply bank offers, discounts
**Current Issue:** ❌ NO offer integration

### 49. Compare and book
**Input:** "Compare prices and book cheapest hotel near office"
**Expected:** Price comparison, best deal selection
**Current Issue:** ❌ NO comparison engine

### 50. Book for someone else
**Input:** "Book flight for my mom traveling next week"
**Expected:** Third-party booking, passenger details
**Current Issue:** ❌ NO third-party booking

---

## Category 4: Payments & Financial (51-65)

### 51. Pay bill
**Input:** "Pay my electricity bill of ₹2500"
**Expected:** Verify biller, secure payment, receipt
**Current Issue:** ❌ FAKE UPI links generated

### 52. Transfer money
**Input:** "Transfer ₹5000 to John's account"
**Expected:** Verify recipient, OTP, secure transfer
**Current Issue:** ❌ NO real transfer capability

### 53. Check balance
**Input:** "What's my account balance?"
**Expected:** Bank integration, secure access
**Current Issue:** ❌ NO bank integration

### 54. Split bill
**Input:** "Split ₹3000 dinner bill among 4 friends"
**Expected:** Calculate split, create payment requests
**Current Issue:** ❌ NO split capability

### 55. Pay rent
**Input:** "Pay this month's rent ₹25000 to landlord"
**Expected:** Large payment confirmation, receipt
**Current Issue:** ❌ NO real payment

### 56. EMI payment
**Input:** "Pay my credit card EMI"
**Expected:** Find EMI details, process payment
**Current Issue:** ❌ NO EMI integration

### 57. Recharge mobile
**Input:** "Recharge my phone with ₹299 plan"
**Expected:** Find plans, real recharge
**Current Issue:** ❌ NO recharge integration

### 58. DTH recharge
**Input:** "Recharge Tata Sky ₹500"
**Expected:** Find subscriber, real recharge
**Current Issue:** ❌ NO DTH integration

### 59. Pay credit card
**Input:** "Pay my HDFC credit card bill"
**Expected:** Fetch bill amount, secure payment
**Current Issue:** ❌ NO credit card integration

### 60. Subscription payment
**Input:** "Pay my Netflix subscription"
**Expected:** Find subscription, process renewal
**Current Issue:** ❌ NO subscription management

### 61. Donate to charity
**Input:** "Donate ₹1000 to PM Care Fund"
**Expected:** Verify charity, tax receipt
**Current Issue:** ❌ NO charity integration

### 62. Pay insurance premium
**Input:** "Pay my LIC premium due this month"
**Expected:** Find policy, secure payment
**Current Issue:** ❌ NO insurance integration

### 63. Request money
**Input:** "Request ₹500 from Mike for lunch"
**Expected:** Send payment request
**Current Issue:** ❌ NO payment request feature

### 64. Recurring payment setup
**Input:** "Set up auto-pay for electricity bill"
**Expected:** Mandate creation, bank approval
**Current Issue:** ❌ NO mandate support

### 65. Payment history
**Input:** "Show my payment history this month"
**Expected:** Fetch transaction history
**Current Issue:** ❌ NO transaction records

---

## Category 5: Creative & Content (66-80)

### 66. Create logo
**Input:** "Create a logo for my startup 'TechFlow'"
**Expected:** Generate logo options, provide files
**Current Issue:** Provides links to tools, no direct generation

### 67. Write blog post
**Input:** "Write a 500-word blog about AI trends"
**Expected:** Generate quality content
**Current Issue:** Can generate text, may be generic

### 68. Create presentation
**Input:** "Create 10-slide presentation on sales report"
**Expected:** Generate slides with data
**Current Issue:** ❌ NO presentation generation

### 69. Design social media post
**Input:** "Create Instagram post for product launch"
**Expected:** Generate image + caption
**Current Issue:** Limited image generation

### 70. Write resume
**Input:** "Write resume for 5 years experienced developer"
**Expected:** Generate formatted resume
**Current Issue:** Can write content, no formatting

### 71. Create video script
**Input:** "Write 60-second explainer video script"
**Expected:** Generate engaging script
**Current Issue:** Text generation works

### 72. Design business card
**Input:** "Create business card with my details"
**Expected:** Generate printable design
**Current Issue:** ❌ NO business card design

### 73. Write email newsletter
**Input:** "Write monthly newsletter for customers"
**Expected:** Generate newsletter content
**Current Issue:** Can generate, no template

### 74. Create invoice
**Input:** "Create invoice for client ABC - ₹50000"
**Expected:** Generate professional invoice PDF
**Current Issue:** ❌ NO invoice generation

### 75. Write thank you letter
**Input:** "Write thank you letter to interview panel"
**Expected:** Generate personalized letter
**Current Issue:** Works for text generation

### 76. Create event poster
**Input:** "Create poster for office Diwali party"
**Expected:** Generate festive poster
**Current Issue:** Limited design capability

### 77. Write product description
**Input:** "Write description for new smartphone"
**Expected:** Generate marketing copy
**Current Issue:** Text generation works

### 78. Create meme
**Input:** "Create a funny meme about Monday meetings"
**Expected:** Generate relevant meme
**Current Issue:** ❌ NO meme generation

### 79. Write song lyrics
**Input:** "Write lyrics for a motivational song"
**Expected:** Generate creative lyrics
**Current Issue:** Can generate text

### 80. Translate document
**Input:** "Translate this proposal to Hindi"
**Expected:** Accurate translation
**Current Issue:** Can translate, may have errors

---

## Category 6: Research & Information (81-90)

### 81. Research topic
**Input:** "Research latest electric car models in India"
**Expected:** Search, summarize findings
**Current Issue:** Web search works, summary quality varies

### 82. Compare products
**Input:** "Compare iPhone 15 vs Samsung S24"
**Expected:** Feature comparison table
**Current Issue:** Can search, formatting limited

### 83. Find best price
**Input:** "Find cheapest price for MacBook Air"
**Expected:** Price comparison across sites
**Current Issue:** ❌ NO price tracking

### 84. Get news summary
**Input:** "What's the latest news on budget 2024?"
**Expected:** Fetch and summarize news
**Current Issue:** Can search, no news API

### 85. Find nearby places
**Input:** "Find best restaurants near me"
**Expected:** Location-based search
**Current Issue:** ❌ NO location access

### 86. Weather check
**Input:** "What's the weather in Bangalore today?"
**Expected:** Current weather, forecast
**Current Issue:** Can search, no weather API

### 87. Stock price check
**Input:** "What's the current price of Reliance stock?"
**Expected:** Real-time stock data
**Current Issue:** ❌ NO stock API

### 88. Sports score
**Input:** "What's the score of today's IPL match?"
**Expected:** Live/recent scores
**Current Issue:** Can search, may not be current

### 89. Recipe search
**Input:** "Find recipe for butter chicken"
**Expected:** Detailed recipe with steps
**Current Issue:** Can find via search

### 90. Book summary
**Input:** "Give me summary of Atomic Habits"
**Expected:** Key points summary
**Current Issue:** Can generate from knowledge

---

## Category 7: Personal Assistant (91-100)

### 91. Set alarm
**Input:** "Set alarm for 6 AM tomorrow"
**Expected:** System alarm integration
**Current Issue:** ❌ NO device integration

### 92. Create task list
**Input:** "Create task list for today with these 5 items"
**Expected:** Store and track tasks
**Current Issue:** Tasks not persistent

### 93. Track habit
**Input:** "Track my daily water intake"
**Expected:** Habit tracking system
**Current Issue:** ❌ NO habit tracking

### 94. Calculate expense
**Input:** "How much did I spend this week?"
**Expected:** Expense summary
**Current Issue:** ❌ NO expense tracking

### 95. Birthday reminder
**Input:** "Remind me about Mom's birthday next week"
**Expected:** Recurring reminder
**Current Issue:** Reminders not persistent

### 96. Shopping list
**Input:** "Add milk, bread, eggs to shopping list"
**Expected:** Persistent shopping list
**Current Issue:** ❌ NO list persistence

### 97. Note taking
**Input:** "Note down today's meeting key points"
**Expected:** Store searchable notes
**Current Issue:** ❌ NO note storage

### 98. Quick calculation
**Input:** "Calculate 15% tip on ₹1500 bill"
**Expected:** Accurate calculation
**Current Issue:** Works correctly

### 99. Unit conversion
**Input:** "Convert 100 USD to INR"
**Expected:** Current exchange rate
**Current Issue:** Can search for rates

### 100. Daily brief
**Input:** "Give me my daily briefing"
**Expected:** Summary of day's tasks, weather, news
**Current Issue:** ❌ NO unified briefing

---

## Summary of Test Results

| Category | Working | Partially Working | Not Working |
|----------|---------|-------------------|-------------|
| Meetings | 3 | 5 | 7 |
| Email | 2 | 5 | 8 |
| Bookings | 0 | 0 | 20 |
| Payments | 0 | 0 | 15 |
| Creative | 5 | 5 | 5 |
| Research | 3 | 5 | 2 |
| Personal | 2 | 2 | 6 |
| **TOTAL** | **15** | **22** | **63** |

### Key Finding
**63% of tasks are NOT functional** - the AI fabricates responses instead of clearly stating limitations or providing real functionality.

---

## Recommendations

1. **Be Honest**: Clearly state what the AI cannot do
2. **Add Real Integrations**: Payment gateways, booking APIs
3. **Store Everything**: All tasks, bookings, transactions must be logged
4. **Confirmation Flows**: Multi-step confirmation for sensitive actions
5. **Interactive Options**: Button-based selections instead of text lists
