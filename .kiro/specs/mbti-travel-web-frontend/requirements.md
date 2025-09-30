# Requirements Document

## Introduction

This document outlines the requirements for a Vue + TypeScript web frontend application that provides an interactive interface for the MBTI Travel Assistant. The application will be created in the `mbti-travel-web-frontend` project folder and will allow users to input their MBTI personality type and receive personalized 3-day Hong Kong travel itineraries with customizable recommendations for tourist spots and restaurants.

## Requirements

### Requirement 1: Authentication and Security

**User Story:** As a user, I want secure access to the MBTI Travel Planner so that my travel planning session is protected and authenticated.

#### Acceptance Criteria

1. WHEN a user accesses the application without a valid Cognito JWT token THEN the system SHALL redirect them to a login page
2. WHEN a user has a valid JWT token THEN the system SHALL allow access to the main application
3. WHEN making API requests to the MBTI travel assistant MCP endpoint THEN the system SHALL include the JWT token in the request headers
4. IF the JWT token expires during use THEN the system SHALL handle token refresh or redirect to login

### Requirement 2: MBTI Personality Input Interface

**User Story:** As a user, I want to input my MBTI personality type through an intuitive interface so that I can receive personalized travel recommendations.

#### Acceptance Criteria

1. WHEN the user accesses the main page THEN the system SHALL display a centered flex box containing all input elements
2. WHEN displaying the interface THEN the system SHALL show a header "Hong Kong MBTI Travel Planner"
3. WHEN displaying the interface THEN the system SHALL show a subheader "Welcome to MBTI Travel Planner for traveling Hong Kong"
4. WHEN the text input is empty THEN the system SHALL display placeholder text "E.g. ENFP, INTJ, INFJ..."
5. WHEN the user types in the text box THEN the system SHALL limit input to four capital alphabetic characters
6. WHEN displaying the interface THEN the system SHALL show a button labeled "Get my 3 days itinerary!"
7. WHEN displaying the interface THEN the system SHALL show a link "Don't know your MBTI type? Take the test here" that opens www.16personalities.com

### Requirement 3: MBTI Input Validation

**User Story:** As a user, I want the system to validate my MBTI input so that I receive accurate personality-based recommendations.

#### Acceptance Criteria

1. WHEN the user clicks the submit button THEN the system SHALL validate the input against valid MBTI personality codes
2. IF the input is not a valid MBTI code THEN the system SHALL display "Please input correct MBTI Personality!" and keep the user on the current page
3. IF the input is valid THEN the system SHALL proceed to submit the request to the MCP endpoint
4. WHEN validation passes THEN the system SHALL accept only these 16 valid codes: INTJ, INTP, ENTJ, ENTP, INFJ, INFP, ENFJ, ENFP, ISTJ, ISFJ, ESTJ, ESFJ, ISTP, ISFP, ESTP, ESFP

### Requirement 4: API Integration and Loading State

**User Story:** As a user, I want to see progress feedback while my itinerary is being generated so that I know the system is working.

#### Acceptance Criteria

1. WHEN a valid MBTI input is submitted THEN the system SHALL display "Generating Itinerary in progress..." message
2. WHEN making the API request THEN the system SHALL include the JWT token in the request headers
3. WHEN the API request is in progress THEN the system SHALL show a loading state for approximately 100 seconds
4. WHEN the API response is received THEN the system SHALL navigate to the itinerary display page
5. IF the API request fails THEN the system SHALL display an appropriate error message

### Requirement 5: Itinerary Display Page Header

**User Story:** As a user, I want clear navigation and context on the itinerary page so that I can understand my personalized results and navigate back if needed.

#### Acceptance Criteria

1. WHEN the itinerary page loads THEN the system SHALL display a "Back" button to return to the input page
2. WHEN the itinerary page loads THEN the system SHALL display "Hong Kong MBTI Travel Planner" in large fonts
3. WHEN the itinerary page loads THEN the system SHALL display "3-Day Itinerary for [MBTI Personality] Personality" with the personality type highlighted in a different color and background
4. WHEN the user clicks the "Back" button THEN the system SHALL navigate to the MBTI input page

### Requirement 6: Itinerary Content Structure

**User Story:** As a user, I want to see my 3-day itinerary in a clear, organized format so that I can easily understand my travel plan.

#### Acceptance Criteria

1. WHEN displaying the itinerary THEN the system SHALL show an outer flex box with header "Your Personalized 3-Day Hong Kong Itinerary"
2. WHEN displaying the itinerary THEN the system SHALL show a table format by default (unless personality-specific customization applies)
3. WHEN creating the table THEN the system SHALL have columns for: empty header, Day 1, Day 2, Day 3
4. WHEN creating the table THEN the system SHALL have rows for: Breakfast, Morning Session, Lunch, Afternoon Session, Dinner, Night Session
5. WHEN displaying content cells THEN the system SHALL use combo boxes for all recommendations with selectable alternatives
6. WHEN a combo box selection changes THEN the system SHALL update the displayed data in that cell

### Requirement 7: Restaurant Data Display

**User Story:** As a user, I want to see detailed restaurant information in my itinerary so that I can make informed dining choices.

#### Acceptance Criteria

1. WHEN displaying restaurant recommendations THEN the system SHALL show the restaurant name in the combo box
2. WHEN a restaurant is selected THEN the system SHALL display relevant restaurant data including address, district, price range
3. WHEN restaurant data is available THEN the system SHALL include meal type, sentiment data, location category, and operating hours
4. WHEN displaying operating hours THEN the system SHALL show separate hours for Mon-Fri, Sat-Sun, and Public Holiday
5. WHEN restaurant sentiment data is available THEN the system SHALL display likes, dislikes, and neutral feedback appropriately

### Requirement 8: Tourist Spot Data Display

**User Story:** As a user, I want to see comprehensive tourist spot information so that I can understand why each location fits my personality and plan my visits effectively.

#### Acceptance Criteria

1. WHEN displaying tourist spot recommendations THEN the system SHALL show the spot name in the combo box
2. WHEN a tourist spot is selected THEN the system SHALL display the MBTI personality it best fits
3. WHEN tourist spot data is available THEN the system SHALL include address, district, area, and operating hours
4. WHEN displaying operating hours THEN the system SHALL show separate hours for Mon-Fri, Sat-Sun, and Public Holiday
5. WHEN tourist spot data includes remarks THEN the system SHALL display additional information like telephone numbers
6. WHEN description data is available THEN the system SHALL store it for personality-specific display requirements

### Requirement 9: MBTI Personality-Specific Customizations - Structured Types

**User Story:** As a user with a structured personality type (INTJ, ENTJ, ISTJ, ESTJ), I want time management features so that I can plan my itinerary with specific timing.

#### Acceptance Criteria

1. WHEN the user's MBTI is INTJ, ENTJ, ISTJ, or ESTJ THEN the system SHALL display a textbox for each session labeled "target start / end time"
2. WHEN the user's MBTI is ENTJ THEN the system SHALL additionally display checkboxes for each tourist spot labeled "important!"
3. WHEN time input fields are displayed THEN the system SHALL allow users to specify preferred timing for each activity

### Requirement 10: MBTI Personality-Specific Customizations - Flexible Types

**User Story:** As a user with a flexible personality type (INTP, ISTP, ESTP), I want a simplified view format so that I can see my itinerary in a more casual, point-form layout.

#### Acceptance Criteria

1. WHEN the user's MBTI is INTP, ISTP, or ESTP THEN the system SHALL display the itinerary in point form notes for each day instead of a table
2. WHEN displaying point form THEN the system SHALL organize recommendations by day with bullet points
3. WHEN the user's MBTI is ESTP THEN the system SHALL additionally display flashy styling and emojis
4. WHEN the user's MBTI is ESTP THEN the system SHALL show placeholder image links for tourist spots

### Requirement 11: MBTI Personality-Specific Customizations - Colorful Types

**User Story:** As a user with a creative personality type (ENTP, INFP, ENFP, ISFP), I want a vibrant, visually appealing interface so that my travel planning experience matches my personality.

#### Acceptance Criteria

1. WHEN the user's MBTI is ENTP, INFP, ENFP, or ISFP THEN the system SHALL display the interface with colorful styling
2. WHEN the user's MBTI is ENTP, INFP, ENFP, or ISFP THEN the system SHALL show placeholder image links beside each tourist spot
3. WHEN displaying colorful themes THEN the system SHALL use vibrant color schemes appropriate for creative personalities
4. WHEN placeholder images are shown THEN the system SHALL indicate where actual images would be displayed

### Requirement 12: MBTI Personality-Specific Customizations - Feeling Types

**User Story:** As a user with a feeling-oriented personality type (INFJ, ISFJ, ENFJ, ESFJ), I want detailed descriptions and social features so that I can understand the emotional connection to places and share with others.

#### Acceptance Criteria

1. WHEN the user's MBTI is INFJ or ISFJ THEN the system SHALL display the "description" field for each tourist spot
2. WHEN the user's MBTI is ENFJ or ESFJ THEN the system SHALL display a textbox for each session labeled "Group Notes:"
3. WHEN the user's MBTI is ENFJ or ESFJ THEN the system SHALL show a placeholder "Share with friends" link
4. WHEN the user's MBTI is ISFJ THEN the system SHALL use warm color tones for the display

### Requirement 13: Color Theme Customization

**User Story:** As a user, I want the interface colors to reflect my personality type so that the application feels personalized to me.

#### Acceptance Criteria

1. WHEN displaying the itinerary THEN the system SHALL apply personality-specific color themes to the table and text
2. WHEN the system assigns colors THEN each of the 16 MBTI personalities SHALL have a unique color tone
3. WHEN applying color themes THEN the system SHALL ensure text remains readable and accessible
4. WHEN color customization is applied THEN the system SHALL maintain consistent theming throughout the itinerary display

### Requirement 14: Responsive Design and User Experience

**User Story:** As a user, I want the application to work well on different devices so that I can plan my travel from anywhere.

#### Acceptance Criteria

1. WHEN accessing the application on different screen sizes THEN the system SHALL display responsively
2. WHEN using mobile devices THEN the system SHALL maintain usability of combo boxes and input fields
3. WHEN displaying tables on smaller screens THEN the system SHALL ensure content remains accessible
4. WHEN navigation elements are displayed THEN the system SHALL be easily clickable on touch devices

### Requirement 15: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when something goes wrong so that I can understand what happened and how to proceed.

#### Acceptance Criteria

1. WHEN API requests fail THEN the system SHALL display user-friendly error messages
2. WHEN network connectivity issues occur THEN the system SHALL provide appropriate feedback
3. WHEN validation errors occur THEN the system SHALL clearly indicate what needs to be corrected
4. WHEN loading states are active THEN the system SHALL provide visual feedback to indicate progress
5. IF the JWT token becomes invalid THEN the system SHALL handle the authentication error gracefully