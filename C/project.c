#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Define the Student node structure
struct Student {
    int id;
    char name[50];
    float marks;
    struct Student* next;  // Pointer to next node
};

// Function to add a student at the beginning of the list
struct Student* addStudent(struct Student* head, int id, char* name, float marks) {
    struct Student* newNode = (struct Student*)malloc(sizeof(struct Student));
    newNode->id = id;
    strcpy(newNode->name, name);
    newNode->marks = marks;
    newNode->next = head; // link new node to existing list
    return newNode;       // new node becomes head
}

// Function to display all students
void displayStudents(struct Student* head) {
    struct Student* temp = head;
    printf("\nID\tName\t\tMarks\n");
    printf("-----------------------------\n");
    while(temp != NULL) {
        printf("%d\t%-10s\t%.2f\n", temp->id, temp->name, temp->marks);
        temp = temp->next;
    }
}

// Function to save linked list data to a file
void saveToFile(struct Student* head, char* filename) {
    FILE* fp = fopen(filename, "w");
    if(fp == NULL) {
        printf("Error opening file!\n");
        return;
    }
    struct Student* temp = head;
    while(temp != NULL) {
        fprintf(fp, "%d,%s,%.2f\n", temp->id, temp->name, temp->marks);
        temp = temp->next;
    }
    fclose(fp);
    printf("Data saved to %s successfully.\n", filename);
}

// Function to load data from file into linked list
struct Student* loadFromFile(char* filename) {
    FILE* fp = fopen(filename, "r");
    if(fp == NULL) {
        printf("File not found, starting with empty list.\n");
        return NULL;
    }

    struct Student* head = NULL;
    int id;
    char name[50];
    float marks;

    // Read lines in format: id,name,marks
    while(fscanf(fp, "%d,%49[^,],%f\n", &id, name, &marks) == 3) {
        head = addStudent(head, id, name, marks); // insert at beginning
    }

    fclose(fp);
    return head;
}

int main() {
    struct Student* head = NULL;
    int choice;
    int id;
    char name[50];
    float marks;

    // Load students from file
    head = loadFromFile("students.txt");

    while(1) { // infinite menu loop
        printf("\n--- Student Management ---\n");
        printf("1. Add Student\n2. Display Students\n3. Save & Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch(choice) {
            case 1:
                printf("Enter ID: ");
                scanf("%d", &id);
                printf("Enter Name: ");
                scanf(" %[^\n]", name);  // Read string with spaces
                printf("Enter Marks: ");
                scanf("%f", &marks);
                head = addStudent(head, id, name, marks);
                break;
            case 2:
                displayStudents(head);
                break;
            case 3:
                saveToFile(head, "students.txt");
                printf("Exiting program.\n");
                exit(0);
            default:
                printf("Invalid choice! Please try again.\n");
        }
    }

    return 0;
}