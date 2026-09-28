import json
import pickle
from pathlib import Path

import faiss
import numpy as np

# Thư mục chứa file dữ liệu FAISS
_FAISS_DIR = Path(__file__).resolve().parent

# Chiều embedding mặc định của ArcFace
_DEFAULT_DIM = 512


class FaissService:
    def __init__(
        self, embeddings: np.ndarray = None, ids: np.ndarray = None, names: list = None
    ):
        self.data: dict = {}
        self.id_to_name_dict: dict = {}
        if embeddings is None or ids is None:
            loaded = self.load_data()
            if loaded and self.data:
                ids = np.array(list(self.data.keys()), dtype=np.int64)
                embeddings = np.array(list(self.data.values()), np.float32)
                self.faiss_model = faiss.IndexIDMap2(
                    faiss.IndexFlatIP(embeddings.shape[1])
                )
                self.faiss_model.add_with_ids(embeddings, ids)
            else:
                self.faiss_model = faiss.IndexIDMap2(faiss.IndexFlatIP(_DEFAULT_DIM))
        else:
            if len(embeddings) != len(set(ids)):
                self.faiss_model = faiss.IndexIDMap2(faiss.IndexFlatIP(_DEFAULT_DIM))
                return
            self.faiss_model = faiss.IndexIDMap2(faiss.IndexFlatIP(embeddings.shape[1]))
            self.faiss_model.add_with_ids(embeddings, ids)
            self.data = dict(zip(ids.tolist(), embeddings.tolist()))
            self.id_to_name_dict = dict(zip([str(i) for i in ids.tolist()], names))
            self.save_data()

    def add(self, new_id: int, new_embedding: np.ndarray, new_name: str):
        new_id = int(new_id)
        if new_id in list(self.data.keys()):
            print(f"{new_id} already in the current data")

            return False
        else:
            self.faiss_model.add_with_ids(
                new_embedding, np.array([new_id], dtype=np.int64)
            )
            self.data[new_id] = new_embedding.tolist()[0]
            self.id_to_name_dict[str(new_id)] = new_name
            self.save_data()

            return True

    def delete(self, id: int):
        id = int(id)
        if id not in list(self.data.keys()):
            return False
        else:
            self.faiss_model.remove_ids(np.array([id], np.int64))
            self.data.pop(id, None)
            self.id_to_name_dict.pop(str(id), None)
            self.save_data()

            return True

    def update(self, new_id: int, new_embedding: np.ndarray, new_name: str):
        if self.delete(new_id):
            if self.add(new_id, new_embedding, new_name):
                return True
        return False

    def search(self, query_embedding, k=1, threshold=0.4):
        if not self.data:
            return "", ""
        D, I = self.faiss_model.search(query_embedding, k)
        if D[0][0] > threshold and str(I[0][0]) in self.id_to_name_dict:
            return int(I[0][0]), self.id_to_name_dict[str(I[0][0])]
        return "", ""

    def save_data(self):
        with open(_FAISS_DIR / "embedding2id.pkl", "wb") as f:
            pickle.dump(self.data, f)

        with open(_FAISS_DIR / "id2name.json", "w", encoding="utf-8") as file:
            json.dump(self.id_to_name_dict, file, indent=4, ensure_ascii=False)

    def load_data(self) -> bool:
        try:
            with open(_FAISS_DIR / "embedding2id.pkl", "rb") as f:
                self.data = pickle.load(f)

            with open(_FAISS_DIR / "id2name.json", "r", encoding="utf-8") as file:
                self.id_to_name_dict = json.load(file)
            return True
        except Exception as e:
            print("Can not find data:", e)
            self.data = {}
            self.id_to_name_dict = {}
            return False
