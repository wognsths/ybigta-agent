## Database Agent


1. 실행 절차
```{bash}
# 루트 디렉토리에서 실행
docker-compose up -d --build
```

```{bash}
# 데이터 넣어주기
docker cp .\seed_users.sql ybigta-postgres:/tmp/

docker exec -it ybigta-postgres psql -U postgres -d postgres -f /tmp/seed_users.sql
# INSERT 0 10 이 뜨면 정상
```

2. http://localhost:10001/ 에서 다음과 같은 쿼리 실행해보기

```
{
    "query": "What function do you have? Can you check the schema and table available? And if table there is a table, i want 5 sample data. If there is just one table only, don't ask me again, just give me data sample",
    "session_id": "string"
}
```

3. http://localhost:8080/ 에서 코드 이것저것 실행해보기