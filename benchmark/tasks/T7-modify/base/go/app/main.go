package main

import (
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	_ "github.com/mattn/go-sqlite3"
)

var secret = []byte("benchmark-secret")
var db *sql.DB

type Login struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type Item struct {
	ID          int     `json:"id"`
	Name        string  `json:"name"`
	Description *string `json:"description"`
	Price       float64 `json:"price"`
	CreatedAt   string  `json:"created_at"`
}

func sha256hex(s string) string {
	h := sha256.Sum256([]byte(s))
	return base64.StdEncoding.EncodeToString(h[:])
}

func initDB() {
	var err error
	_, err = os.Stat("test.db")
	fresh := os.IsNotExist(err)
	db, err = sql.Open("sqlite3", "test.db")
	if err != nil {
		panic(err)
	}
	if fresh {
		schema, _ := os.ReadFile("data/schema.sql")
		if _, err := db.Exec(string(schema)); err != nil {
			panic(err)
		}
	}
	h := sha256hex("secret")
	db.Exec("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", "admin", h)
}

func auth() gin.HandlerFunc {
	return func(c *gin.Context) {
		header := c.GetHeader("Authorization")
		tokenStr := strings.TrimPrefix(header, "Bearer ")
		token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
			return secret, nil
		})
		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(401, gin.H{"error": "Invalid token"})
			return
		}
		c.Next()
	}
}

func main() {
	initDB()
	r := gin.Default()

	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"ok": true})
	})

	r.POST("/auth/login", func(c *gin.Context) {
		var body Login
		if err := c.ShouldBindJSON(&body); err != nil {
			c.JSON(400, gin.H{"error": "invalid body"})
			return
		}
		var stored string
		err := db.QueryRow("SELECT password FROM users WHERE username=?", body.Username).Scan(&stored)
		if err != nil || stored != sha256hex(body.Password) {
			c.JSON(401, gin.H{"error": "Incorrect username or password"})
			return
		}
		tok := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
			"sub": body.Username, "exp": time.Now().Add(time.Hour).Unix(),
		})
		signed, _ := tok.SignedString(secret)
		c.JSON(200, gin.H{"token": signed})
	})

	r.POST("/items", auth(), func(c *gin.Context) {
		var in struct {
			Name        string  `json:"name"`
			Description *string `json:"description"`
			Price       float64 `json:"price"`
		}
		if err := c.ShouldBindJSON(&in); err != nil {
			c.JSON(400, gin.H{"error": "invalid body"})
			return
		}
		res, err := db.Exec("INSERT INTO items (name, description, price) VALUES (?,?,?)", in.Name, in.Description, in.Price)
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		id, _ := res.LastInsertId()
		c.JSON(201, gin.H{"id": id, "name": in.Name, "description": in.Description, "price": in.Price})
	})

	r.GET("/items", auth(), func(c *gin.Context) {
		rows, _ := db.Query("SELECT id, name, description, price, created_at FROM items")
		defer rows.Close()
		var out []Item
		for rows.Next() {
			var it Item
			rows.Scan(&it.ID, &it.Name, &it.Description, &it.Price, &it.CreatedAt)
			out = append(out, it)
		}
		if out == nil {
			out = []Item{}
		}
		c.JSON(200, out)
	})

	r.GET("/items/:id", auth(), func(c *gin.Context) {
		var it Item
		err := db.QueryRow("SELECT id, name, description, price, created_at FROM items WHERE id=?", c.Param("id")).
			Scan(&it.ID, &it.Name, &it.Description, &it.Price, &it.CreatedAt)
		if err != nil {
			c.JSON(404, gin.H{"error": "not found"})
			return
		}
		c.JSON(200, it)
	})

	r.PUT("/items/:id", auth(), func(c *gin.Context) {
		var in struct {
			Name        string  `json:"name"`
			Description *string `json:"description"`
			Price       float64 `json:"price"`
		}
		if err := c.ShouldBindJSON(&in); err != nil {
			c.JSON(400, gin.H{"error": "invalid body"})
			return
		}
		res, _ := db.Exec("UPDATE items SET name=?, description=?, price=? WHERE id=?", in.Name, in.Description, in.Price, c.Param("id"))
		n, _ := res.RowsAffected()
		if n == 0 {
			c.JSON(404, gin.H{"error": "not found"})
			return
		}
		c.JSON(200, gin.H{"message": "updated"})
	})

	r.DELETE("/items/:id", auth(), func(c *gin.Context) {
		res, _ := db.Exec("DELETE FROM items WHERE id=?", c.Param("id"))
		n, _ := res.RowsAffected()
		if n == 0 {
			c.JSON(404, gin.H{"error": "not found"})
			return
		}
		c.Status(204)
	})

	r.Run("0.0.0.0:8005")
}
