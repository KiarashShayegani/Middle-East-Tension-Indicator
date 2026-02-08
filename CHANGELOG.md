# Changelog
All notable changes to the Middle-East Tension Index will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2] - 2026-01
### Added
- Professional dark theme UI with custom CSS styling
- Multi-timeframe analysis (1H, 4H, 1D, 1W) with configurable weights
- Asset cards showing real-time prices and percentage changes
- Session state management for persistent timeframe selection
- Enhanced gauge visualization with threshold markers and delta indicators

### Changed
- Updated asset weighting based on historical correlation analysis
- Improved error handling for Yahoo Finance API calls
- Restructured code into modular functions for better maintainability
- Enhanced documentation with version-specific README files

### Fixed
- Resolved auto_adjust deprecation warnings in yfinance
- Fixed layout issues on smaller screens
- Corrected normalization formula edge cases

## [v0.1] - 2025-10
### Initial Release
- Basic 4-asset monitoring (Crude Oil, Gold, Bitcoin, Lockheed Martin)
- Simple weighted tension calculation formula
- Basic Streamlit dashboard with gauge visualization
- 3-minute auto-refresh for real-time updates
- Manual refresh button option

### Known Issues
- Limited to market hours data only
- No historical data persistence
- Basic error handling only
