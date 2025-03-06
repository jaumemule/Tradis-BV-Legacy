package main

import (
  "fmt"
  "encoding/json"
  "net/http"
  "bytes"
  "io/ioutil"
  "github.com/julienschmidt/httprouter"
	"log"
	"os"
)

const WalletBaseUrl = "http://api:3000/api/v1/wallet"

type Order struct {
  TargetCurrency string `json:"targetCurrency"`
  BaseCurrency string `json:"baseCurrency"`
  Quantity string `json:"quantity"`
  Rate string `json:"rate"`
}

func main() {

  // CREATE A LISTENING SERVER
  router := httprouter.New()
	router.GET("/", indexHandler)
	router.GET("/buy", buyOrdersHandler)
	router.GET("/sell", sellOrdersHandler)
  
	// print env
	env := os.Getenv("ENVIRONMENT")
	if env == "production" {
		log.Println("Running api server in production mode")
	} else {
		log.Println("Running api server in dev mode")
	}

  http.ListenAndServe(":3003", router)
  
  // while(true) {
  //   predictions := getAIPredictions()
  //
  //   ordersToExecute := getOrdersToExecute(predictions)
  //
  //   for i := range ordersToExecute {
  //     sendOrderToWallet(ordersToExecute[i])
  //   }
  // }
}

type BittrexOrder struct {
  Orders []Order `json:"bittrex"`
}

func indexHandler(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	fmt.Fprintf(w, "Health is OK")
}

func buyOrdersHandler(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
  buyOrders := []Order{
    Order{TargetCurrency: "BTC", BaseCurrency: "LTC", Quantity: "0.10", Rate:"0.10"},
  }
  buy(buyOrders)
}

func sellOrdersHandler(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
  sellOrders := []Order{
    Order{TargetCurrency: "ETH", BaseCurrency: "BTC", Quantity: "0.00000001", Rate:"0.00000000001"},
  }
  sell(sellOrders)
}

func sell(orders []Order) {
    sellUrl := WalletBaseUrl + "/sell"

    bOrder := BittrexOrder{Orders: orders}

    jsonOrder, _ := json.Marshal(bOrder)

    sendOrderToApi(sellUrl, jsonOrder)
}

func buy(orders []Order) {
  buyUrl := WalletBaseUrl + "/buy"

  bOrder := BittrexOrder{Orders: orders}

  jsonOrder, _ := json.Marshal(bOrder)

  sendOrderToApi(buyUrl, jsonOrder)
}

func sendOrderToApi(url string , jsonOrder []byte) {
  req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonOrder))
  req.Header.Set("client-secret", "id")
  req.Header.Set("client-id", "secret")
  req.Header.Set("Content-Type", "application/json")

  client := &http.Client{}
  resp, err := client.Do(req)

  if err != nil {
    panic(err)
  }

  defer resp.Body.Close()
  body, _ := ioutil.ReadAll(resp.Body)
  
  fmt.Println("response Body:", string(body))
}

// func getAIPredictions() {
//     // Fetch predictions for AI system
// }
//
// func getOrdersToExecute(predictions aray)  {
//     // Given an input of predictions get the orders to execute on the exchanges
// }
//
// func sendOrderToWallet(order)  {
//     // Send order to wallet to get executed
// }
