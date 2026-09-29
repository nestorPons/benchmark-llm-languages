package main

import (
	"github.com/gin-gonic/gin"
	"github.com/jmoiron/sqlx"
	_ "github.com/mattn/go-sqlite3"
	"github.com/dgrijalva/jwt-go"
	"net/http"
	"time"
	"os"
	"fmt"
	"strconv"
)

var db *sqlx.DB

type Item struct {
	ID          int       `db:"id" json:"id"`
	Name        string    `db:"name" json:"name"`
	Description string    `db:"description" json:"description"`
	Price       float64   `db:"price" json:"price"`
	CreatedAt   time.Time `db:"created_at" json:"created_at"`
}

type Credentials struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

var jwtKey = []byte("my_secret_key")

type Claims struct {
	Username string `json:"username"`
	jwt.StandardClaims
}

func main() {
	var err error
	db, err = sqlx.Connect("sqlite3", "./data/items.db")
	if err != nil {
		panic(err)
	}

	router := gin.Default()

	router.GET("/health", healthCheck)
	router.POST("/auth/login", login)

	protected := router.Group("/", authMiddleware)
	{
		protected.POST("/items", createItem)
		protected.GET("/items", getItems)
		protected.GET("/items/:id", getItem)
		protected.PUT("/items/:id", updateItem)
		protected.DELETE("/items/:id", deleteItem)
	}

	router.Run(":8005")
}

func healthCheck(c *gin.Context) {
	c.Status(http.StatusOK)
}

func login(c *gin.Context) {
	var creds Credentials
	if err := c.BindJSON(&creds); err != nil {
		c.Status(http.StatusBadRequest)
		return
	}

	if creds.Username != "admin" || creds.Password != "secret" {
		c.Status(http.StatusUnauthorized)
		return
	}

	expirationTime := time.Now().Add(5 * time.Minute)
	claims := &Claims{
		Username: creds.Username,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: expirationTime.Unix(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(jwtKey)
	if err != nil {
		c.Status(http.StatusInternalServerError)
		return
	}

	c.JSON(http.StatusOK, gin.H{"token": tokenString})
}

func authMiddleware(c *gin.Context) {
	tokenString := c.GetHeader("Authorization")
	if tokenString == "" {
		c.Status(http.StatusUnauthorized)
		c.Abort()
		return
	}

	claims := &Claims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		return jwtKey, nil
	})

	if err != nil || !token.Valid {
		c.Status(http.StatusUnauthorized)
		c.Abort()
		return
	}

	c.Next()
}

func createItem(c *gin.Context) {
	var item Item
	if err := c.BindJSON(&item); err != nil {
		c.Status(http.StatusBadRequest)
		return
	}

	if item.Price < 0 {
		c.Status(http.StatusBadRequest)
		return
	}

	item.CreatedAt = time.Now()
	result, err := db.NamedExec(`INSERT INTO items (name, description, price, created_at) VALUES (:name, :description, :price, :created_at)`, &item)
	if err != nil {
		c.Status(http.StatusInternalServerError)
		return
	}

	id, err := result.LastInsertId()
	if err != nil {
		c.Status(http.StatusInternalServerError)
		return
	}

	item.ID = int(id)
	c.JSON(http.StatusCreated, item)
}

func getItems(c *gin.Context) {
	var items []Item
	err := db.Select(&items, "SELECT * FROM items")
	if err != nil {
		c.Status(http.StatusInternalServerError)
		return
	}

	c.JSON(http.StatusOK, items)
}

func getItem(c *gin.Context) {
	id := c.Param("id")
	var item Item
	err := db.Get(&item, "SELECT * FROM items WHERE id = ?", id)
	if err != nil {
		c.Status(http.StatusNotFound)
		return
	}

	c.JSON(http.StatusOK, item)
}

func updateItem(c *gin.Context) {
	id := c.Param("id")
	var item Item
	if err := c.BindJSON(&item); err != nil {
		c.Status(http.StatusBadRequest)
		return
	}

	if item.Price < 0 {
		c.Status(http.StatusBadRequest)
		return
	}

	item.ID, _ = strconv.Atoi(id)
	_, err := db.NamedExec(`UPDATE items SET name = :name, description = :description, price = :price WHERE id = :id`, &item)
	if err != nil {
		c.Status(http.StatusInternalServerError)
		return
	}

	c.JSON(http.StatusOK, item)
}

func deleteItem(c *gin.Context) {
	id := c.Param("id")
	_, err := db.Exec("DELETE FROM items WHERE id = ?", id)
	if err != nil {
		c.Status(http.StatusInternalServerError)
		return
	}

	c.Status(http.StatusNoContent)
}