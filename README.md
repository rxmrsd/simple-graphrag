# はじめに
今回は，前回の記事でたどり着くことができなかった，GraphRAGについて記載します．[graphrag](https://github.com/microsoft/graphrag)というmicrosoftが提供しているOSSを利用して，簡単なGraphRAG構築します．

# GraphRAGとは

そもそもGraph RAGの意義は，RAG(検索拡張生成：Retrieval-Augmented Generation)という，ドキュメントをベクトルにして，それをもとに回答させる手法を発展させることです．RAGでは，そのドキュメントに含まれる固有名詞の背景や関係性までを汲み取ることができません．指示代名詞が何を指しているのかも前後の文脈で分かる部分であるため，これらを明確にするためGraphを用いるアプローチです．つまり，関係性をわかるようにして，それを判断材料に含めてLLMに回答させることで，より精度の良い結果を得ることを目指しています．

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3618319/1e28fef0-5189-a372-af34-27f4cfa46343.png)


# お題

今回も懲りずに，私の最も好きな漫画である「進撃の巨人」を題材にします．元となるドキュメントは，[進撃の巨人Wikipedia](https://ja.wikipedia.org/wiki/%E9%80%B2%E6%92%83%E3%81%AE%E5%B7%A8%E4%BA%BA)から物語に関連する部分を自分で抜粋したものです．


# graphragを触ってみる
graphragはCLIを提供しており，設定を調整すること以外はコマンド実行で完結することができます．これ以下は基本的に[Get Started](https://microsoft.github.io/graphrag/posts/get_started/)の内容に沿って実行していきます．

## Initialize

まずは初期化を行ないます．所定のフォルダ内に今回用いるドキュメントを格納し，下記コマンドを実行します．

```bash
poetry run python -m graphrag.index --init --root ./ragtest
```

## 各種設定

上記の初期化を行なうと，`root`フォルダ下に，.envファイルとsettings.yamlファイルが作成されます．ここに諸々の設定を記載します．.envファイルには，`GRAPHRAG_API_KEY`にOpenAIのAPI keyを記述，settings.yamlには，利用するモデルやchunkサイズが記述されているので，適宜修正します．

```yaml:settings.yaml(抜粋)
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat # or azure_openai_chat
  model: gpt-4o-mini

chunks:
  size: 100
  overlap: 20
  group_by_columns: [id]
```

## Prompt Tuning

テンプレートで提供されるプロンプトを，今回の元データに即した内容にチューニングします．

```bash
poetry run python -m graphrag.prompt_tune --root ./ragtest --config settings.yaml --language Japanese
```

### チューニング結果

チューニングしたことで，entityを抽出する際のプロンプトに変化が生じました．下記(折りたたみ)のように，few-shotの中に，今回のドキュメントに沿った内容が反映されています．


<details><summary>entity_extractionのプロンプト</summary>

```text:entity_extraction.txt

-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [tribe, person, event, giant, military organization, power, memory, battle, location, historical figure]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. Return output in Japanese as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

4. If you have to translate into Japanese, just translate the descriptions, nothing else!

5. When finished, output {completion_delimiter}.

-Examples-
######################

Example 1:

entity_types: [tribe, person, event, giant, military organization, power, memory, battle, location, historical figure]
text:
洞察力と先見性を持つ。


年表


古代
紀元前970年ごろ
「エルディア」という名の部族は、他部族へ侵略を繰り返し、捕虜にした他部族民たちを奴隷として使役していた。
ユミルという名の奴隷の少女（すなわち「始祖ユミル」）が罪のためエルディアの部落から「追放」され、人狩りから逃げている最中にある巨大な木の中の池に落ち、巨人の起源となる（「大地の悪魔」と呼ば
------------------------
output:
("entity"{tuple_delimiter}エルディア{tuple_delimiter}部族{tuple_delimiter}「エルディア」という名の部族は、他部族へ侵略を繰り返し、捕虜にした他部族民たちを奴隷として使役していた。)
{record_delimiter}
("entity"{tuple_delimiter}ユミル{tuple_delimiter}人物{tuple_delimiter}ユミルという名の奴隷の少女は、エルディアの部落から「追放」され、人狩りから逃げている最中にある巨大な木の中の池に落ち、巨人の起源となる。)
{record_delimiter}
("entity"{tuple_delimiter}巨人{tuple_delimiter}巨人{tuple_delimiter}ユミルが落ちた池から生まれた存在で、巨人の起源とされる。)
{record_delimiter}
("relationship"{tuple_delimiter}ユミル{tuple_delimiter}エルディア{tuple_delimiter}ユミルはエルディアの部落から追放された。{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}ユミル{tuple_delimiter}巨人{tuple_delimiter}ユミルは池に落ちたことで巨人の起源となった。{tuple_delimiter}9)
{completion_delimiter}
#############################


Example 2:

entity_types: [tribe, person, event, giant, military organization, power, memory, battle, location, historical figure]
text:
ての「壁」が崩落し、壁内にいた全ての超大型巨人が解放されたことで多数の死傷者が出る。
アニの硬質化が強制的に解ける。
エレンが始祖の力を使いすべてのエルディア人に｢地鳴らし｣の宣言をする。
幾千万の超大型巨人とエレンがパラディ島からマーレへ侵攻する。
アニ、ヒッチと接触し行動を共にする。
ジークの「叫び」によって発生した巨人は全て掃討されるが、殆どのマ
------------------------
output:
("entity"{tuple_delimiter}超大型巨人{tuple_delimiter}巨人{tuple_delimiter}壁内にいた全ての超大型巨人が解放され、多数の死傷者が出た。)
{record_delimiter}
("entity"{tuple_delimiter}エレン{tuple_delimiter}人{tuple_delimiter}エレンが始祖の力を使い、すべてのエルディア人に「地鳴らし」の宣言をした。)
{record_delimiter}
("entity"{tuple_delimiter}アニ{tuple_delimiter}人{tuple_delimiter}アニは硬質化が強制的に解け、ヒッチと接触し行動を共にした。)
{record_delimiter}
("entity"{tuple_delimiter}ヒッチ{tuple_delimiter}人{tuple_delimiter}ヒッチはアニと接触し、行動を共にした。)
{record_delimiter}
("entity"{tuple_delimiter}ジーク{tuple_delimiter}人{tuple_delimiter}ジークの「叫び」によって発生した巨人は全て掃討された。)
{record_delimiter}
("entity"{tuple_delimiter}パラディ島{tuple_delimiter}場所{tuple_delimiter}エレンが超大型巨人と共にマーレへ侵攻する出発点。)
{record_delimiter}
("entity"{tuple_delimiter}マーレ{tuple_delimiter}場所{tuple_delimiter}エレンと超大型巨人が侵攻する先。)
{record_delimiter}
("relationship"{tuple_delimiter}エレン{tuple_delimiter}超大型巨人{tuple_delimiter}エレンが始祖の力を使い、超大型巨人を指揮してマーレへ侵攻した。{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}アニ{tuple_delimiter}ヒッチ{tuple_delimiter}アニはヒッチと接触し、行動を共にした。{tuple_delimiter}7)
{record_delimiter}
("relationship"{tuple_delimiter}ジーク{tuple_delimiter}超大型巨人{tuple_delimiter}ジークの「叫び」によって発生した巨人は全て掃討された。{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}エレン{tuple_delimiter}パラディ島{tuple_delimiter}エレンが超大型巨人と共にパラディ島からマーレへ侵攻した。{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}エレン{tuple_delimiter}マーレ{tuple_delimiter}エレンが超大型巨人と共にマーレへ侵攻した。{tuple_delimiter}8)
{completion_delimiter}
#############################



-Real Data-
######################
entity_types: [tribe, person, event, giant, military organization, power, memory, battle, location, historical figure]
text: {input_text}
######################
output:
```


</details>

## Indexing

ここからが実際にGraphを構築するプロセスになります．プロセスの中では，6つのPhaseに分かれた処理を行なっています([Indexing Dataflow](https://microsoft.github.io/graphrag/posts/index/1-default_dataflow/))．内部でLLMを用いており，先ほどチューニングをしたPromptを利用します．

1. Compose TextUnits: ドキュメントをチャンクに分割
2. Graph Extraction: LLMを用いてEntities, Relationships，Claimsを抽出
3. Graph Augumentation: グラフから階層的なコミュニティを抽出し，Graph Embeddingを生成
4. Community Summarization: 各階層ごとのコミュニティの情報をLLMを用いて要約
5. Document Processing: ドキュメントをテキストユニットにリンクし，Text Embeddingを生成
6. Network Visualization: 次元削減を行なって，ネットワーク可視化のための2D表現を生成

実際は下記コマンドを実行するだけで完了してしまいます．

```bash
poetry run python -m graphrag.index --root ./ragtest
```


## Graphの確認

Indexingを実行すると，`root`フォルダ下に，`output`フォルダができます．その中に，`create_final_*.parquet`などのファイルが出力されています．中身は下図のようなデータフレームになっています．

(create_final_relationships.parquet)
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3618319/1a7d74bf-2c91-3338-4912-c2bc0c131fe6.png)

興味本位で，上記Relationshipsを可視化したところ，下図のようになりました．「エレン」「ジーク」「調査兵団」から多くの触手が伸びていることがわかります．githubに[このhtmlファイル](https://github.com/rxmrsd/simple-graphrag/blob/main/attack_on_graph.html)を格納しているので，ご興味あれば眺めてみてください．

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3618319/30e08652-802b-f243-b654-cac284d04435.png)

## Query

さて，ここまででGraphを構築することができたので，実際にLLMに質問し，このGraphをもとに回答させようと思います．graphragが持っている機能には，2種類(Local QueryとGlobal Query)があります．それぞれ名前の通り，局所的な関係に対する質問と，Graph全体に対する質問に対して回答を生成します．
下記，Queryの結果になります．どちらも適切に回答している印象です．

### Local Query

```bash
poetry run python -m graphrag.query --root ./ragtest --method local "エレンと幼馴染の人物はどんな特徴がありますか？"
```

この質問には，まず幼馴染が誰なのか特定し，そしてその人の特徴を探索するという，Graphをたどって回答しているようです．回答のもととなるリソースも記述されており，Relationshipsが使われているようです．


:::note info
質問：
エレンと幼馴染の人物はどんな特徴がありますか？

<details><summary>↓↓回答：(長いので折りたたんでいます)↓↓</summary>

SUCCESS: Local Search Response:
エレン・イェーガーの幼馴染には、アルミン・アルレルトとミカサ・アッカーマンがいます。それぞれの特徴について詳しく見ていきましょう。

### アルミン・アルレルト
アルミンは、知恵と戦略に優れたキャラクターであり、エレンとミカサの友人です。彼は第104期訓練兵団の一員として、エレンと共に壁外への夢を語り合った幼馴染です。アルミンは特にエレンを導く重要な役割を担っており、彼の知恵を駆使して仲間を助ける姿勢が彼のキャラクターの重要な要素となっています。彼は非力ではありますが、作戦立案の能力に秀でており、仲間たちとの関係を深めていく中で成長を遂げています [Data: Entities (16, 254); Relationships (120, 250)]。

### ミカサ・アッカーマン
ミカサは、エレンの親友であり、彼を守るために戦う姿勢を持っています。彼女もまた第104期訓練兵団の一員であり、エレンとアルミンの幼馴染です。ミカサは優れた身体能力を持ち、巨人討伐において傑出した才能があります。彼女の強い絆と戦う意志は、物語の重要な要素となっており、エレンに対する深い思いが彼女の行動に影響を与えています [Data: Entities (12, 253); Relationships (205, 277)]。

### まとめ
エレンの幼馴染であるアルミンとミカサは、それぞれ異なる特徴を持ちながらも、共に巨人討伐に挑む仲間として重要な役割を果たしています。アルミンは知恵と戦略に優れ、ミカサは身体能力に秀でたキャラクターであり、彼らの絆は物語の中で大きな意味を持っています。

</details>

:::

### Global Query

```bash
poetry run python -m graphrag.query --root ./ragtest --data output/20240916-111521/artifacts --method global "この物語の中で，彼らはどんなことを成し遂げましたか？"
```

この質問には，community_reportsを用いて回答しているようです．全体の内容を掴むために作成したReportsが役に立って回答している模様です．


:::note
質問：
この物語の中で，彼らはどんなことを成し遂げましたか？

<details><summary>↓↓回答：(長いので折りたたんでいます)↓↓</summary>

SUCCESS: Global Search Response:
## 物語の中での成し遂げたこと

この物語において、主要なキャラクターたちはそれぞれの役割を果たし、様々な成果を上げています。以下に、彼らの成し遂げたことをまとめます。

### エレン・イェーガーの貢献

エレン・イェーガーは、物語の中心的なキャラクターとして、巨人との戦いにおいて重要な役割を果たしました。彼はパラディ島のリーダーとして、島の防衛と攻撃の両面で活躍し、特に超大型巨人と共にマーレに侵攻したことが物語の進行に大きな影響を与えました [Data: Reports (78, 102)]。また、彼の巨人化能力は仲間たちを鼓舞し、戦局において決定的な役割を果たしました [Data: Reports (74)]。

### 調査兵団の活動

調査兵団は、巨人に対抗するための戦闘を行い、特にエルヴィン団長の指導の下でのシガンシナ区の奪回作戦や女型の巨人の捕獲作戦は、彼らの活動の中でも特に重要な位置を占めています [Data: Reports (94)]。彼らの戦略や士気は、物語のテーマである犠牲や勇気を強調する要素となりました [Data: Reports (77)]。

### ジークの影響

ジークは「獣の巨人」としての力を持ち、彼の「叫び」によって巨人が発生し、エルディア人戦士隊や調査兵団との関係が複雑に絡み合っています。彼の行動はエルディア国の運命に直接的な影響を与えています [Data: Reports (90)]。

### ヒストリアのリーダーシップ

ヒストリアは新政権を樹立し、社会的な問題に取り組む姿勢を見せることで、彼女のリーダーシップが物語において重要な変化をもたらしました。彼女は孤児院を開設し、人々から尊敬される存在となりました [Data: Reports (60)]。彼女の決断は他のキャラクターとの関係性に大きな影響を与えています [Data: Reports (44)]。

### 仲間たちの絆

エレンとミカサの強い絆は、共に戦闘に参加し、互いを救うために協力し合うことで物語の中心的な要素となっています [Data: Reports (84)]。また、104期訓練兵団のメンバーは、エレンの奪還作戦に参加し、彼らの団結と信頼が物語の進行において重要な役割を果たしました [Data: Reports (31)]。

## 結論

この物語において、キャラクターたちはそれぞれの役割を通じて、巨人との戦い、社会の変革、仲間との絆を深めることに成功しました。彼らの行動は物語の進行に大きな影響を与え、各キャラクターの成長や変化を促す要因となっています。

</details>
:::

# シンプルなRAGとの比較
シンプルなRAGとの比較をして，Graphを構築することの優位性を確認します．プロンプトなど諸々異なるところはありますが，下記のように，同じ質問に対して，表面的な回答をしたり，回答できなかったりしており，Graphを構築したときのほうが，精度良く回答できている印象です．

:::note warn
質問：
エレンとアルミンの関係性は？
回答：
*エレンとアルミンは幼馴染で、深い信頼関係があります。エレンはアルミンを大切に思っており、彼の意見を尊重します。アルミンもエレンを支える存在であり、彼の行動を理解しようと努力しています。二人は困難な状況でも互いに助け合い、強い絆を築いています。全体として、彼らの関係は友情と相互理解に基づいています。*
:::
:::note warn
質問：
エレンと幼馴染の人物はどんな特徴がありますか？
回答：
*エレンの幼馴染は、彼と強い絆を持っており、互いに深い理解があります。彼はエレンを支える存在であり、時には彼に対して厳しい意見を述べることもあります。外見や性格の詳細はコンテキストに記載されていないため、具体的な特徴はわかりません。全体として、彼は信頼できる友人として描かれています。*
:::
:::note warn
質問：
この物語の中で，彼らはどんなことを成し遂げましたか？
回答：
*わからない。*

:::

# 料金, 処理時間
今回用いたドキュメント(約23,000字)に対し，GraphRAGでかかったコストは以下です．モデルはgpt4o-miniを用いたため，大きなコストはかからなかったという印象です．


| 処理 | コスト | 時間 |
|:-----------|------------:|:------------:|
| indexing | $0.4 | 15分 |
| local query | $0.06 | 数秒 |
| global query | $0.01 | 数秒 |


# まとめ

今回は前回のリベンジとして，GraphRAGを実践しました．graphragを用いることで，Graphを構築し，それをもとに回答することができました．ただし前回述べたように，Entityの抽出には課題があるようです．同義なのに別のEntityとして扱われたり，固有名詞の抽出がうまくできていない箇所があったりしました．まだまだ発展途上の分野ですので，引き続きウォッチしていきたいです．
今回のコードや成果物は[こちら](https://github.com/rxmrsd/simple-graphrag)に格納しています．ご参考まで．


# 参考
- [進撃の巨人 Wikipedia](https://ja.wikipedia.org/wiki/%E9%80%B2%E6%92%83%E3%81%AE%E5%B7%A8%E4%BA%BA)
- [graphrag](https://microsoft.github.io/graphrag/)
- [Enhancing RAG-based application accuracy by constructing and leveraging knowledge graphs](https://blog.langchain.dev/enhancing-rag-based-applications-accuracy-by-constructing-and-leveraging-knowledge-graphs/)
- [話題のGraphRAGとは](https://www.alpha.co.jp/blog/202408_01/)