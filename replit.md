# Player Rating Progression Analyzer

## Overview

A Streamlit-based web application for analyzing and visualizing player rating progressions over time. The application allows users to upload CSV files containing match data between players, including their ratings before matches, and provides interactive visualizations to track rating changes and performance trends. Built for sports analytics, gaming tournaments, or any competitive scenario where player ratings evolve based on match outcomes.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Streamlit Framework**: Single-page web application using Streamlit for rapid prototyping and deployment
- **Interactive Visualizations**: Plotly Express and Plotly Graph Objects for creating dynamic, interactive charts and graphs
- **Wide Layout**: Configured for maximum screen utilization to display complex data visualizations
- **File Upload Interface**: Built-in CSV upload functionality with real-time validation and error handling

### Data Processing Pipeline
- **Pandas Data Processing**: Core data manipulation using pandas DataFrames for efficient CSV parsing and data transformation
- **Data Validation**: Multi-layer validation including column presence checks, date parsing validation, and numeric rating verification
- **Error Handling**: Comprehensive error handling with user-friendly error messages and suggestions for data format corrections
- **Data Cleaning**: Automatic removal of rows with missing critical values while preserving data integrity

### Visualization System
- **Rating Progression Charts**: Time-series visualizations showing player rating changes over match history
- **Interactive Charts**: Plotly-based charts allowing for zooming, filtering, and hover interactions
- **Multi-player Analysis**: Support for tracking multiple players simultaneously with color-coded progression lines

### Data Schema Requirements
- **Match Data Structure**: Expects CSV files with specific column structure:
  - `player1`: First player identifier
  - `player2`: Second player identifier  
  - `date`: Match date in recognizable datetime format
  - `rating p1`: Player 1's rating at time of match
  - `rating p2`: Player 2's rating at time of match

## External Dependencies

### Python Libraries
- **streamlit**: Web application framework for building the user interface
- **pandas**: Data manipulation and analysis library for CSV processing
- **plotly**: Interactive visualization library (both express and graph_objects modules)
- **datetime**: Standard library for date/time handling
- **io**: Standard library for file input/output operations

### Data Format Dependencies
- **CSV File Format**: Application designed specifically for comma-separated value files
- **Date Format Flexibility**: Supports multiple date formats including YYYY-MM-DD and MM/DD/YYYY
- **Numeric Rating System**: Expects numeric rating values that can be converted to float data types

### Deployment Platform
- **Streamlit Cloud Ready**: Architecture designed for easy deployment on Streamlit's cloud platform
- **Replit Compatible**: Single-file structure makes it suitable for Replit deployment and sharing