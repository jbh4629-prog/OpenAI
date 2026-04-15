# Feynman 프로젝트를 Codespace에 별도로 생성하기

요청하신 대로 `.devcontainer` 동작은 바꾸지 않고,
**원할 때 수동으로 실행하는 생성 스크립트**만 제공합니다.

## 사용 방법

새 Codespace에서 아래 1회 실행:

```bash
bash scripts/create-feynman-project.sh
```

기본적으로 현재 저장소 아래 `feynman/` 폴더를 만들고,
`https://github.com/getcompanion-ai/feynman`를 clone + 의존성 설치까지 진행합니다.

다른 폴더명으로 만들고 싶으면:

```bash
bash scripts/create-feynman-project.sh my-feynman
```

## 다음 단계

```bash
cd feynman
npm run build
npm test
```
