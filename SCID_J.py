import openai
import os


def load_api_key(file_path):
    try:
        with open(file_path, "r") as file:
            api_key = file.read().strip()
            return api_key
    except Exception as e:
        print(f"API 키를 불러오는 중 오류 발생: {e}")
        return None


# 현재 파일과 동일한 폴더에 있는 'api_key.txt' 파일의 절대 경로를 가져옵니다.
api_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")

# 경로가 제대로 설정되었는지 확인하기 위해 출력해 봅니다.
print(f"API 키 파일 경로: {api_key_file}")

openai.api_key = load_api_key(api_key_file)


# DSM-5 정신장애 범주
DSM5_CATEGORIES = {
    "1. 조현병 스펙트럼 장애": "Schizophrenia Spectrum Disorder",
    "2. 신경발달장애": "Neurodevelopmental Disorder",
    "3. 양극성 및 관련 장애": "Bipolar and Related Disorder",
    "4. 우울장애": "Depressive Disorder",
    "5. 불안장애": "Anxiety Disorder",
    "6. 강박 및 관련 장애": "Obsessive-Compulsive and Related Disorder",
    "7. 외상 및 스트레스 사건 관련 장애": "Trauma- and Stressor-Related Disorder",
    "8. 해리장애": "Dissociative Disorder",
    "9. 신체증상 및 관련 장애": "Somatic Symptom and Related Disorder",
    "10. 급식 및 섭식장애": "Feeding and Eating Disorder",
    "11. 배설장애": "Elimination Disorder",
    "12. 수면-각성 장애": "Sleep-Wake Disorder",
    "13. 성기능 장애": "Sexual Dysfunction",
    "14. 성불편증": "Gender Dysphoria",
    "15. 파괴적, 충동통제 및 품행장애": "Disruptive, Impulse-Control, and Conduct Disorder",
    "16. 물질 관련 및 중독 장애": "Substance-Related and Addictive Disorder",
    "17. 신경인지장애": "Neurocognitive Disorder",
    "18. 성격장애": "Personality Disorder",
    "19. 성도착 장애": "Paraphilic Disorder",
    "20. 기타 정신장애": "Other Mental Disorders",
}

# ICD-10-CM 범주 및 코드 매핑
ICD10_CM_CODES = {
    "Mental, Behavioral and Neurodevelopmental disorders": "F01-F99",
    "Diseases of the nervous system": "G00-G99",
    "Diseases of the eye and adnexa": "H00-H59",
    "Diseases of the ear and mastoid process": "H60-H95",
    "Diseases of the circulatory system": "I00-I99",
    "Diseases of the respiratory system": "J00-J99",
    "Diseases of the digestive system": "K00-K95",
    "Diseases of the skin and subcutaneous tissue": "L00-L99",
    "Diseases of the musculoskeletal system and connective tissue": "M00-M99",
    "Diseases of the genitourinary system": "N00-N99",
}


class GPT4AdjustmentDisorderDiagnosis:
    def __init__(self):
        self.diagnosis_criteria = {
            "J1": False,
            "J2": False,
            "J3": False,
            "J4": False,
            "J5": False,
        }
        self.final_diagnosis = []
        self.dsm5_diagnosis = None
        self.icd10_code = None
        self.user_input = ""

    def ask_gpt(self, question):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a diagnostic assistant. Please answer based on DSM-5 and SCID-5 guidelines.",
                    },
                    {
                        "role": "user",
                        "content": f"User input: {self.user_input}\n\nQuestion: {question}",
                    },
                ],
                max_tokens=1000,
            )
            answer = response["choices"][0]["message"]["content"].strip()
            print(f"질문: {question}")
            print(f"GPT 응답: {answer}")

            # "예" 또는 "아니오"가 포함되지 않으면 유추하도록 수정
            if "예" in answer:
                return "예"
            elif "아니오" in answer:
                return "아니오"
            # 관대하게 판단: 특정 키워드 포함 시 "예"로 간주
            elif any(
                keyword in answer
                for keyword in ["스트레스", "증상 시작", "발병", "악화", "애도"]
            ):
                return "예"
            else:
                return "모호함"
        except Exception as e:
            print(f"오류 발생: {e}")
            return None

    def ask_patient(self, question):
        # 환자로부터 직접 입력을 받는 함수
        return input(f"{question}\n")

    def initial_evaluation(self):
        # DSM-5 정신장애 범주를 먼저 확인
        question = "사용자의 증상이 다른 DSM-5 장애에 해당하나요?"
        response = self.ask_gpt(question)

        if response in DSM5_CATEGORIES.values():
            self.dsm5_diagnosis = response
            print(f"DSM-5 진단 결과: {response}")
            self.icd10_code = self.map_to_icd10(response)
            print(f"ICD-10-CM 코드: {self.icd10_code}")
            print("SCID-5 종료.")
            return False  # SCID-5 종료

        return True  # 적응장애 평가로 진행

    def map_to_icd10(self, dsm5_category):
        # DSM-5 진단에 해당하는 ICD-10-CM 코드 반환
        if "정신장애" in dsm5_category:
            return ICD10_CM_CODES["Mental, Behavioral and Neurodevelopmental disorders"]
        elif "신경" in dsm5_category:
            return ICD10_CM_CODES["Diseases of the nervous system"]
        else:
            return "ICD-10 코드 없음"

    def gather_information(self):
        # J1: 스트레스 원 확인 및 3개월 이내에 증상 발병
        question = "스트레스 원이 확인되었으며 증상이 3개월 이내에 발병했습니까?"
        response = self.ask_gpt(question)
        if response == "예":
            self.diagnosis_criteria["J1"] = True
            print("J1: 해당됨. J2로 넘어갑니다.")
        elif response == "아니오":
            print("J1: 해당 안됨. 적응장애 해당 없음.")
            return False
        else:  # 모호한 응답에 대해 추가 질문
            print("J1: 추가 질문 필요")
            additional_question = self.ask_patient(
                "무슨 일이 일어났는지에 대해 말해주십시오. 당신은 (스트레스 원)이 (증상)의 발병과 어떤 관련이 있다고 생각합니까?"
            )

            # 사건의 종류에 따라 추가 질문 분기
            if "단일 사건" in additional_question:
                follow_up_question = "(스트레스 원)이 있은 지 얼마 후에 (증상)이 처음 발병했습니까? (3개월 이내였습니까?)"
            else:
                follow_up_question = "(스트레스 원)이 있은 지 얼마 후에 (증상)이 처음 발병했습니까? (3개월 이내였습니까?)"

            follow_up_response = self.ask_patient(follow_up_question)
            if follow_up_response == "예":
                self.diagnosis_criteria["J1"] = True
                print("J1: 해당됨. J2로 넘어갑니다.")
            else:
                print("J1: 해당 안됨. 적응장애 해당 없음.")
                return False

        # J2: 사회적/직업적 기능에 현저한 장애 또는 고통
        question = "증상이 사회적, 직업적, 중요한 기능 영역에 현저한 장애 또는 고통을 유발하는가?"
        response = self.ask_gpt(question)
        if response == "예":
            self.diagnosis_criteria["J2"] = True
            print("J2: 해당됨. J3로 넘어갑니다.")
        elif response == "아니오":
            print("J2: 해당 안됨. 적응장애 해당 없음.")
            return False
        else:  # 모호한 응답에 대해 추가 질문
            print("J2: 추가 질문 필요")
            additional_question = self.ask_patient(
                "(증상)이 당신의 삶에 어떤 영향을 미쳤습니까?"
            )

            # 최초 상태 정보를 기반으로 관련 질문 생성 및 판단
            relevant_questions = []
            if "관계" in additional_question:
                relevant_questions.append(
                    "(증상)이 다른 사람과의 관계에 어떻게 영향을 미쳤습니까?"
                )
            if "직업" in additional_question:
                relevant_questions.append(
                    "(증상)이 직업/학업에 어떻게 영향을 미쳤습니까?"
                )
            if "가정" in additional_question:
                relevant_questions.append("(증상이 가정에 어떻게 영향을 미쳤습니까?)")

            for sub_question in relevant_questions:
                follow_up_response = self.ask_patient(sub_question)
                if (
                    "예" in follow_up_response or "어려움" in follow_up_response
                ):  # 응답에 '어려움'이 있으면 True로 판단
                    self.diagnosis_criteria["J2"] = True
                    print("J2: 해당됨. J3로 넘어갑니다.")
                    break
            if not self.diagnosis_criteria["J2"]:
                print("J2: 해당 안됨. 적응장애 해당 없음.")
                return False

        # J3: 다른 정신질환의 악화가 아닌가
        question = "증상이 다른 정신질환의 악화가 아니며, 이전에 그런 반응을 경험한 적이 없습니까?"
        response = self.ask_gpt(question)
        if response == "예":
            self.diagnosis_criteria["J3"] = True
            print("J3: 해당됨. J4로 넘어갑니다.")
        elif response == "아니오":
            print("J3: 해당 안됨. 적응장애 해당 없음.")
            return False
        else:  # 모호한 응답에 대해 추가 질문
            print("J3: 추가 질문 필요")
            additional_question = self.ask_patient(
                "이러한 증상이 스트레스 원 이전에도 있었습니까?"
            )
            follow_up_response = self.ask_patient(additional_question)
            if follow_up_response == "아니요":  # '아니요'일 때 J3는 True가 되어야 함.
                self.diagnosis_criteria["J3"] = True
                print("J3: 해당됨. J4로 넘어갑니다.")
            else:
                print("J3: 해당 안됨. 적응장애 해당 없음.")
                return False

        # J4: 정상 애도 반응이 아닌가
        question = "증상이 정상적인 애도 반응이 아닌가요?"
        response = self.ask_gpt(question)
        if response == "예":
            self.diagnosis_criteria["J4"] = True
            print("J4: 해당됨. J5로 넘어갑니다.")
        elif response == "아니오":
            print("J4: 해당 안됨. 적응장애 해당 없음.")
            return False
        else:  # 모호한 응답에 대해 추가 질문
            additional_question = self.ask_patient(
                "최근에 애도할 만한 사건(예: 사망)이 있었습니까?"
            )
            follow_up_response = self.ask_patient(additional_question)
            if follow_up_response == "예":
                self.diagnosis_criteria["J4"] = True
                print("J4: 해당됨. J5로 넘어갑니다.")
            else:
                print("J4: 해당 안됨. 적응장애 해당 없음.")
                return False

        # J5: 증상이 스트레스 원 종료 후 6개월 이상 지속되지 않았는가
        question = "스트레스 원 종료 후 증상이 6개월 이상 지속되지 않았습니까?"
        response = self.ask_gpt(question)
        if response == "예":
            self.diagnosis_criteria["J5"] = True
            print("J5: 해당됨. 적응장애 진단됨.")
        elif response == "아니오":
            print("J5: 해당 안됨. 적응장애 해당 없음.")
            return False
        else:  # 모호한 응답에 대해 추가 질문
            additional_question = self.ask_patient(
                "스트레스 원 종료 후 증상이 얼마나 지속되었습니까?"
            )
            follow_up_response = self.ask_patient(additional_question)
            if "6개월" in follow_up_response:
                self.diagnosis_criteria["J5"] = True
                print("J5: 해당됨. 적응장애 진단됨.")
            else:
                print("J5: 해당 안됨. 적응장애 해당 없음.")
                return False

        return True

    def finalize_diagnosis(self):
        if all(self.diagnosis_criteria.values()):
            print("적응장애 진단됨.")
            # 추가 증상 확인 및 출력
            symptoms_question = "환자에게 다음 중 어떤 증상이 있습니까? 우울 기분 동반, 불안 동반, 불안 및 우울 기분 동반, 품행장애 동반, 정서 및 품행장애 동반, 명시되지 않음."
            symptoms = self.ask_gpt(symptoms_question)
            if symptoms:
                # 추가 증상 출력
                print(f"추가 증상: {symptoms}")
                # 증상에 맞는 상세 설명을 추가하여 출력
                symptom_details = {
                    "우울 기분 동반": "저하된 기분, 눈물이 남 또는 무망감이 두드러진다.",
                    "불안 동반": "신경과민, 걱정, 안절부절못함 또는 분리불안이 두드러진다.",
                    "불안 및 우울 기분 동반": "우울과 불안의 조합이 두드러진다.",
                    "품행장애 동반": "품행장애가 두드러진다.",
                    "정서 및 품행장애 동반": "정서 증상(예: 우울, 불안)과 품행장애가 모두 두드러진다.",
                    "명시되지 않음": "적응장애의 특정한 아형의 하나로 분류할 수 없는 부적응 반응이 있는 것이다.",
                }
                for symptom in symptoms.split(", "):
                    if symptom in symptom_details:
                        print(f"{symptom}: {symptom_details[symptom]}")
        else:
            print("적응장애 해당 없음.")

    def diagnose(self, user_input):
        self.user_input = user_input  # 최초로 입력받은 사용자 상태 정보
        # 1차 평가: 적응장애를 고려할 수 있는지 확인
        if self.initial_evaluation():
            # J1~J5 기준을 통해 추가 평가
            if self.gather_information():
                # 최종 진단 결정
                self.finalize_diagnosis()
        else:
            if self.dsm5_diagnosis:
                print(
                    f"최종 진단: {self.dsm5_diagnosis} (ICD-10-CM 코드: {self.icd10_code})"
                )
            else:
                print("적절한 DSM-5 또는 ICD-10-CM 진단을 찾을 수 없습니다.")


# 사용자 입력 예시
user_input = """
환자는 최근 직장에서 상사와의 갈등으로 인해 스트레스를 받았고, 이로 인해 집중력 저하와 불면증이 발생했습니다. 스트레스는 2개월 전 시작되었습니다. 
환자는 이전에 정신질환 진단을 받은 적이 없으며, 가족과의 관계에서도 문제가 발생하고 있습니다. 
"""

# 진단 시스템 실행
diagnosis = GPT4AdjustmentDisorderDiagnosis()
diagnosis.diagnose(user_input)
