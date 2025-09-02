package main
import (
    "context"
    "encoding/json"
    "os"
    "fmt"
    "io"
    "log"
	"net/http"
	"time"
    "bufio"
    "strings"
    "net/url"
  )

const (
	SELFHOSTED_ANALYSIS_URL = "$sonarhost/api/qualitygates/project_status?analysisId=$analysisId"

)
func runReport(ctx context.Context, logger *log.Logger,  sonarHost string, proxyURL string,  sonar_token string, reportTaskFile string, failOnAnalysisFailure bool,  maxRetries int, waitTime int)  (SonarResponse, error) {
    logger.Println("Running sonar analysis extraction")

    // fmt.Println("reportTaskFile: ", reportTaskFile)
    // Open the reportTaskFile
	file, err := os.Open(reportTaskFile)
	if err != nil {
		logger.Println("Error opening file:", reportTaskFile, "error:", err)
		return SonarResponse{}, fmt.Errorf("Error opening file:", reportTaskFile, "error:", err)
	}
	defer file.Close()
	ceTaskUrl:=""

	// Read the file line by line
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		// Skip empty lines and comments
		if len(line) == 0 || strings.HasPrefix(line, "#") {
			continue
		}
		// Split the line into key and value
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			if key == "ceTaskUrl" {
			    ceTaskUrl = value
			    break
			}
		}
	}
	if err := scanner.Err(); err != nil {
		logger.Println("Error reading file:", reportTaskFile , "error", err)
        return SonarResponse{}, fmt.Errorf("Error reading file:", reportTaskFile , "error", err)
	}
	if ceTaskUrl == "" {
		fmt.Printf("ceTaskUrl Key not found")
		return SonarResponse{}, fmt.Errorf("ceTaskUrl Key not found")
	}

	// Add a reusable HTTP client
	var transport *http.Transport

	if proxyURL != "" {
	    logger.Println("Using proxy url")
        proxy, err := url.Parse(proxyURL)
        if err != nil {
            log.Fatal(err)
        }
        transport = &http.Transport{
            Proxy: http.ProxyURL(proxy),
            MaxIdleConns:       100,
            IdleConnTimeout:    30 * time.Second,
            DisableCompression: true,
        }
    }else {
        transport = &http.Transport{
			MaxIdleConns:       100,
			IdleConnTimeout:    30 * time.Second,
			DisableCompression: true,
		}
	}

    var client = &http.Client{
		Timeout: DEFAULT_HTTP_TIMEOUT,
		Transport: transport,
	}

	logger.Println("ceTaskUrl", ceTaskUrl)
	// get the report task
	retries := 0

    var taskResponse SonarTaskResponse
	for retries < maxRetries {
        taskResponse, err = getReport(ctx, client, logger, ceTaskUrl, sonar_token )
        if err != nil {
            logger.Println("Error getting sonar report task", err)
            return SonarResponse{}, fmt.Errorf("Error getting sonar report task", err)
        }
        if taskResponse.Task.Status == "SUCCESS" {
            logger.Println("Sonar analysis task completed successfully after ", retries, " retries")
            break
        }
        if taskResponse.Task.Status == "PENDING" || taskResponse.Task.Status == "IN_PROGRESS" {
            logger.Println("Sonar analysis task is still in progress, waiting for ", waitTime, " seconds before retrying")
            time.Sleep(time.Duration(waitTime) * time.Second)
            retries++
        }
	}
    if (taskResponse.Task.Status != "SUCCESS") {
        logger.Println("Sonar analysis task after ", maxRetries, " retries is ", taskResponse.Task.Status, "exiting")
        return SonarResponse{}, fmt.Errorf("Sonar analysis task after ", maxRetries, " retries is ", taskResponse.Task.Status, "exiting")
    }

	logger.Println("taskResponse.Task.AnalysisId", taskResponse.Task.AnalysisId)
    // get the analysis content
    analysis , err := getAnalysis(ctx, client, logger, sonarHost, sonar_token, taskResponse.Task.AnalysisId)
    if err != nil {
        logger.Println("Error getting sonar analysis report: ", err)
         return SonarResponse{}, fmt.Errorf("Error getting sonar analysis report: ", err)
    }
    if analysis.ProjectStatus.Status != "OK" && failOnAnalysisFailure {
        logger.Println("Sonar analysis failed, exiting according to failOnAnalysisFailure argument")
        return SonarResponse{}, fmt.Errorf("Sonar analysis failed, exiting according to failOnAnalysisFailure argument")
    }

    response := SonarResponse{
        Task: taskResponse.Task,
        Analysis: analysis.ProjectStatus,
    }

    return response, nil
 }


func getReport(ctx context.Context , client *http.Client, logger *log.Logger, ceTaskUrl string, sonar_token string) (SonarTaskResponse, error) {
	 // Make the HTTP GET request
	logger.Println("getReport ceTaskUrl:",ceTaskUrl)
	req, err := http.NewRequestWithContext(ctx, "GET", ceTaskUrl, nil)
	req.Header.Set("Authorization", "Bearer " + sonar_token)
	resp, err := client.Do(req)
	if err != nil {
		return SonarTaskResponse{}, fmt.Errorf("Error making the request, url:",ceTaskUrl, "error", err)
	}

	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
    if err != nil {
        logger.Println("getReport error getting response body error:", err)
        return SonarTaskResponse{}, fmt.Errorf("getReport error getting response body error, url:",ceTaskUrl, "error", err)
    }

	if resp.StatusCode != http.StatusOK {
		return SonarTaskResponse{}, fmt.Errorf("getReport error getting response from", ceTaskUrl, " returned ", resp.StatusCode, " response body ", body)
	}

    logger.Println("getReport resp.StatusCode:", resp.StatusCode)

    var taskResponse SonarTaskResponse
    err = json.Unmarshal(body, &taskResponse)
    if err != nil {
		logger.Println("getReport error Unmarshal response body ", string(body))
		return SonarTaskResponse{}, fmt.Errorf("error unmarshal report response for report", ceTaskUrl, "error",  err)
	}
	logger.Println("getReport taskResponse:", taskResponse)
	return taskResponse, nil
}

func getAnalysis(ctx context.Context, client *http.Client, logger *log.Logger,  sonarHost string, sonar_token string, analysisId string) (SonarAnalysis, error) {

    analysisUrl := strings.Replace(SELFHOSTED_ANALYSIS_URL, "$analysisId", analysisId, 1)
    analysisUrl = strings.Replace(analysisUrl, "$sonarhost", sonarHost, 1)
    logger.Println("analysisId", analysisId)
    logger.Println("sonarhost", sonarHost)
    //logger.Println("analysisUrl", analysisUrl)
	 // Make the HTTP GET request
	req, err := http.NewRequestWithContext(ctx, "GET", analysisUrl , nil)
	req.Header.Set("Authorization", "Bearer " + sonar_token)
	resp, err := client.Do(req)
	if err != nil {
		return SonarAnalysis{}, fmt.Errorf("getAnalysis, Error making the request, url:",analysisUrl, "error", err)
	}
    defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
        logger.Println("getAnalysis error getting response body error:", err)
        return SonarAnalysis{}, fmt.Errorf("getAnalysis error getting response body error, url:",analysisUrl, "error", err)
    }

	if resp.StatusCode != http.StatusOK {
		return SonarAnalysis{}, fmt.Errorf("getAnalysis, error getting response from", analysisUrl, " returned ", resp.StatusCode, " response body ", body)
	}

    var analysisResponse  SonarAnalysis
    err = json.Unmarshal(body, &analysisResponse)
    if err != nil {
		log.Println("getAnalysis, get temp credentials response body ", string(body))
		return SonarAnalysis{}, fmt.Errorf("getAnalysis, error unmarshal analysis response", analysisUrl, "error",  err)
	}

	return analysisResponse, nil
}