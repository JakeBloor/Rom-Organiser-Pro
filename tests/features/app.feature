Feature: ROM Organizer Pro application

  Scenario: Main page loads
    Given the Flask application is configured for testing
    When the homepage is requested
    Then the response status code should be 200
    And the homepage should contain "ROM Organizer Pro"

  Scenario: Logs page loads
    Given the Flask application is configured for testing
    When the logs page is requested
    Then the response status code should be 200
    And the logs page should contain "Log Viewer"

  Scenario: DAT validation loads sample DAT entries
    Given a temporary DAT directory and file exist
    When the DAT files are loaded
    Then the hash lookup should return "Super Mario Bros." for the sample MD5

  Scenario: DAT auto-download runs on startup
    Given DAT fetch and load functions are stubbed
    When initialize_dat_files is called
    Then the DAT fetch function should be invoked
    And the DAT load function should also be invoked
