import express from "express";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

// endpoint utama buat Flutter
app.post("/api/chat", (req, res) => {
  const msg = req.body.msg;
  res.json({
    reply: `Bot menerima: ${msg}`
  });
});

// listen port railway
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("API jalan di port", PORT));
