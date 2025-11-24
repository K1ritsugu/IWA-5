from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import engine, get_db

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contacts API",
    description="CRUD API для управления телефонными контактами",
    version="1.0.0"
)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to Contacts API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.post(
    "/contacts/",
    response_model=schemas.ContactResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Contacts"]
)
def create_contact(
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db)
):
    """Создать новый контакт"""
    # Проверка на существование телефона
    db_contact = db.query(models.Contact).filter(
        models.Contact.phone == contact.phone
    ).first()
    if db_contact:
        raise HTTPException(
            status_code=400,
            detail="Контакт с таким телефоном уже существует"
        )
    
    # Проверка на существование email
    if contact.email:
        db_contact = db.query(models.Contact).filter(
            models.Contact.email == contact.email
        ).first()
        if db_contact:
            raise HTTPException(
                status_code=400,
                detail="Контакт с таким email уже существует"
            )
    
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.get(
    "/contacts/",
    response_model=List[schemas.ContactResponse],
    tags=["Contacts"]
)
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех контактов"""
    contacts = db.query(models.Contact).offset(skip).limit(limit).all()
    return contacts


@app.get(
    "/contacts/{contact_id}",
    response_model=schemas.ContactResponse,
    tags=["Contacts"]
)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    """Получить контакт по ID"""
    contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id
    ).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return contact


@app.put(
    "/contacts/{contact_id}",
    response_model=schemas.ContactResponse,
    tags=["Contacts"]
)
def update_contact(
    contact_id: int,
    contact_update: schemas.ContactUpdate,
    db: Session = Depends(get_db)
):
    """Обновить контакт"""
    db_contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id
    ).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    
    update_data = contact_update.model_dump(exclude_unset=True)
    
    # Проверка уникальности телефона
    if "phone" in update_data:
        existing = db.query(models.Contact).filter(
            models.Contact.phone == update_data["phone"],
            models.Contact.id != contact_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Контакт с таким телефоном уже существует"
            )
    
    # Проверка уникальности email
    if "email" in update_data and update_data["email"]:
        existing = db.query(models.Contact).filter(
            models.Contact.email == update_data["email"],
            models.Contact.id != contact_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Контакт с таким email уже существует"
            )
    
    for key, value in update_data.items():
        setattr(db_contact, key, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.delete(
    "/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Contacts"]
)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Удалить контакт"""
    db_contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id
    ).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    
    db.delete(db_contact)
    db.commit()
    return None


@app.get("/health", tags=["Health"])
def health_check():
    """Проверка работоспособности API"""
    return {"status": "healthy"}