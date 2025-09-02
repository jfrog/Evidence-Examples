package main
import (
    "context"
    "encoding/json"
    "os"
    "log"
	"time"
    "strings"
    "strconv"
  )
  /*
    SonarScanResponse is the json analysis that was outputed by sonar
    and will be returned to the calling build process for cresting an evidence

   notice that the calling client should first check that return value was 0 before using the response JSON,
   otherwise the response is an error message which cannot be parsed
   */
// sonar response struct
type SonarResponse struct {
    Task SonarTask `json:"task"`
    Analysis ProjectStatus `json:"analysis"`
}

// Define a struct to hold the response data
type SonarTaskResponse struct {
	Task SonarTask `json:"task"`
}

type SonarTask struct {
	    id string `json:"id"`
		Status string `json:"status"`
		AnalysisId string `json:"analysisId"`
		ComponentId string `json:"componentId"`
		ComponentKey string `json:"componentKey"`
		ComponentName string `json:"componentName"`
		Organization string `json:"organization"`
		SubmittedAt string `json:"submittedAt"`
		SubmitterLogin string `json:"submitterLogin"`
		StartedAt string `json:"startedAt"`
		ExecutedAt string `json:"executedAt"`
	}
type Condition struct {
	Status         string `json:"status"`
	MetricKey      string `json:"metricKey"`
	Comparator     string `json:"comparator"`
	PeriodIndex    int    `json:"periodIndex"`
	ErrorThreshold string `json:"errorThreshold"`
	ActualValue    string `json:"actualValue"`
}

type Period struct {
	Index int    `json:"index"`
	Mode  string `json:"mode"`
	Date  string `json:"date"`
}

type ProjectStatus struct {
	Status            string      `json:"status"`
	Conditions        []Condition `json:"conditions"`
	Periods           []Period    `json:"periods"`
	IgnoredConditions bool        `json:"ignoredConditions"`
}

type SonarAnalysis struct {
	ProjectStatus ProjectStatus `json:"projectStatus"`
}

const (
	DEFAULT_HTTP_TIMEOUT = 10 * time.Second
	LOG_FILE_LOCATION = "sonar-scan.log"
)
func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	logFile, err := os.OpenFile(LOG_FILE_LOCATION, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
	}
	defer logFile.Close()
	logger := log.New(logFile, "[SONAR EVIDENCE CREATION] ", log.Ldate|log.Ltime|log.Lshortfile)
    logger.Println("Running sonar analysis extraction")
    sonar_token := os.Getenv("SONAR_TOKEN")
    if sonar_token == "" {
        logger.Println("Sonar token not found, set SONAR_TOKEN variable")
        os.Exit(1)
    }
    sonar_type := os.Getenv("SONAR_TYPE")
    if sonar_type == "" {
        sonar_type = "SAAS"
    } else if sonar_type != "SELFHOSTED" && sonar_type != "SAAS" {
        logger.Println("Wrong Sonar type, set SONAR_TYPE variable to either SAAS or SELFHOSTED")
        os.Exit(1)
    }

    //home/runner/work/Evidence-Examples/Evidence-Examples/.scannerwork/report-task.txt
    //get the sonar report file location or details to .scannerwork/.report-task.txt
    reportTaskFile := ".scannerwork/.report-task.txt"
    failOnAnalysisFailure := false
    maxRetries := 1
    waitTime := 5
    proxyURL := ""
    if len(os.Args) > 0 {
        // loop over all args
        for i, arg := range os.Args {
            if i == 0 {
                continue
            }
            if strings.HasPrefix(arg, "--reportTaskFile=") {
                reportTaskFile = strings.TrimPrefix(arg, "--reportTaskFile=")
            } else if strings.HasPrefix(arg, "--FailOnAnalysisFailure") {
                failOnAnalysisFailure = true
            } else if strings.HasPrefix(arg, "--MaxRetries=") {
                maxRetriesStr := strings.TrimPrefix(arg, "--MaxRetries=")
                maxRetries, err = strconv.Atoi(maxRetriesStr)
                if err != nil {
                    logger.Println("Invalid wait time argument:",maxRetriesStr , "error:" ,err)
                    os.Exit(1)
                }
            } else if strings.HasPrefix(arg, "--WaitTime=") {
                waitTimeStr := strings.TrimPrefix(arg, "--WaitTime=")
                waitTime, err = strconv.Atoi(waitTimeStr)
                if err != nil {
                    logger.Println("Invalid wait time argument:",waitTimeStr , "error:" ,err)
                    os.Exit(1)
                }
            } else if strings.HasPrefix(arg, "--UseProxy") {
                proxyURL = os.Getenv("SONAR_PROXY_URL")

                if proxyURL == "" {
                    logger.Println("SONAR_PROXY_URL not found, set SONAR_PROXY_URL variable when using --UseProxy argument")
                    os.Exit(1)
                }
            }
        }
        logger.Println("reportTaskFile:", reportTaskFile)
        logger.Println("FailOnAnalysisFailure:", failOnAnalysisFailure)
        logger.Println("maxRetries:", maxRetries)
        logger.Println("WaitTime:", waitTime)
     }
    response := SonarResponse{}
    defaultSonarHost := "https://sonarcloud.io"
    sonarHost := os.Getenv("SONAR_HOST_URL")

    if sonar_type == "SAAS" {
        if sonarHost == "" {
            sonarHost = defaultSonarHost
        }
        logger.Println("Running sonar analysis extraction for SAAS, host:", sonarHost)

    }else if sonar_type == "SELFHOSTED" {
        if sonarHost == "" {
            logger.Println("Sonar host not found, set SONAR_HOST_URL variable")
            os.Exit(1)
        }
        logger.Println("Running sonar analysis extraction for " , sonar_type,  " server", sonarHost)
    }
    response, err = runReport(ctx, logger, sonarHost, proxyURL, sonar_token, reportTaskFile, failOnAnalysisFailure,  maxRetries, waitTime)

    if err != nil {
        logger.Println("Error in generating report predicate:", err)
        os.Exit(1)
    }

    // marshal the response to JSON
	jsonBytes, err := json.Marshal(response)
	if err != nil {
		logger.Println("Error marshaling JSON", err)
		os.Exit(1)
	}
	// return response to caller through stdout
	os.Stdout.Write(jsonBytes)
 }
