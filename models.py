from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Todo(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    done = Column(Boolean, default=False, nullable=False)

    def as_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'done': self.done
        }

